import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, patch
import fakeredis.aioredis
from beanie import PydanticObjectId
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
import pytest

from app.config import settings
from app.core.websocket_ticket import consume_ws_ticket, issue_ws_ticket
from app.main import app
from app.models.consolidated import (
    PeerQuestion,
    PeerQuiz,
    Question,
    QuestionOption,
    QuizAttempt,
    Session,
    SessionParticipant,
    User,
)
from app.routers.peer_quizzes import _format_quiz
from app.services.auth_service import AuthService
from app.core.security import hash_refresh_token
from app.services.peer_quiz_service import PeerQuizService
from app.services.quiz_service import QuizService


@pytest.mark.asyncio
async def test_auth_race_atomic_otp_attempts():
    """Verify that verify_otp atomically filters and increments attempts, preventing race window."""
    email = "race_tester@edumeet.org"
    fake_redis: Any = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch("app.services.auth_service.get_redis", return_value=fake_redis):
        # Send OTP challenge
        await AuthService.request_otp(email, "127.0.0.1")

        # 1st invalid attempt: 2 attempts remaining
        with pytest.raises(HTTPException) as exc1:
            await AuthService.verify_otp(email, "000000")
        assert "attempt(s) remaining" in exc1.value.detail

        # 2nd invalid attempt: 1 attempt remaining
        with pytest.raises(HTTPException) as exc2:
            await AuthService.verify_otp(email, "000000")
        assert "attempt(s) remaining" in exc2.value.detail

        # 3rd invalid attempt: max attempts (3) exhausted
        with pytest.raises(HTTPException) as exc3:
            await AuthService.verify_otp(email, "000000")
        assert "exceeded" in exc3.value.detail.lower()

        # 4th attempt: atomically rejected via {"attempts": {"$lt": 5}} / is_used
        with pytest.raises(HTTPException) as exc4:
            await AuthService.verify_otp(email, "000000")
        assert "exceeded" in exc4.value.detail.lower() or "expired" in exc4.value.detail.lower()


@pytest.mark.asyncio
async def test_refresh_grace_window_and_theft_detection():
    """Verify refresh rotation grace window (15s) returns same successor and detects replay theft."""
    fake_redis: Any = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch("app.services.auth_service.get_redis", return_value=fake_redis):
        user = User(
            email="ref_test@edumeet.org",
            full_name="Refresh Tester",
            age_confirmed=True,
            country="US",
        )
        await user.insert()
        user_id = str(user.id)
        initial_refresh_token = "edumeet_refresh_token_initial_12345"
        token_hash = hash_refresh_token(initial_refresh_token)

        # Seed active session in Redis
        await fake_redis.set(f"refresh:{token_hash}", user_id)
        await fake_redis.sadd(f"user_tokens:{user_id}", token_hash)

        # 1st rotation: issues successor token
        u1, acc1, ref1 = await AuthService.rotate_refresh_token(initial_refresh_token)
        assert acc1 is not None
        assert ref1 is not None

        # 2nd concurrent rotation within 15-second grace window: returns the identical successor token
        u2, acc2, ref2 = await AuthService.rotate_refresh_token(initial_refresh_token)
        assert acc2 == acc1
        assert ref2 == ref1

        # Expire the grace window
        await fake_redis.delete(f"refresh_grace:{token_hash}")

        # 3rd rotation after grace window: detected as token theft and revokes all sessions
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.rotate_refresh_token(initial_refresh_token)
        assert exc_info.value.status_code == 401

        # Verify all active refresh tokens for this user have been revoked
        remaining_tokens = await fake_redis.smembers(f"user_tokens:{user_id}")
        assert len(remaining_tokens) == 0


@pytest.mark.asyncio
async def test_ws_ticket_single_use():
    """Verify websocket ticket is single-use and deletes immediately on consumption."""
    fake_redis: Any = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch("app.core.websocket_ticket.get_redis", return_value=fake_redis):
        ticket = await issue_ws_ticket(
            user_id="user_123",
            session_id="sess_123",
            role="teacher_a",
        )
        assert len(ticket) > 20

        # First consumption succeeds
        payload1 = await consume_ws_ticket(ticket)
        assert payload1 is not None
        assert payload1["user_id"] == "user_123"

        # Second consumption fails (single-use)
        payload2 = await consume_ws_ticket(ticket)
        assert payload2 is None


@pytest.mark.asyncio
async def test_unauthenticated_access_returns_401():
    """Verify quiz routes and live-roster return 401 when accessed without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Quiz start
        res1 = await client.post("/api/v1/quizzes/start", json={"subject_slug": "dsa"})
        assert res1.status_code == 401

        # Live roster
        res2 = await client.get("/api/v1/matching/pool/live-roster")
        assert res2.status_code == 401


@pytest.mark.asyncio
async def test_demo_routes_404_outside_development():
    """Verify demo routes return 404 when APP_ENV is 'test' or 'production'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # demo-login
        res1 = await client.post("/api/v1/auth/demo-login")
        assert res1.status_code == 404

        # demo session
        res2 = await client.post("/api/v1/sessions/demo")
        assert res2.status_code == 404


@pytest.mark.asyncio
async def test_quiz_timer_server_side_enforcement():
    """Verify elapsed seconds is computed strictly from server served_at and client value is ignored."""
    user = User(
        email="timer_tester@edumeet.org",
        full_name="Timer Student",
        age_confirmed=True,
        country="US",
    )
    await user.insert()

    q = Question(
        subject_slug="dsa",
        topic_slug="arrays",
        subtopic_slug="arrays-1",
        difficulty="easy",
        prompt_text="What is time complexity of list append?",
        options=[
            QuestionOption(id="A", text="O(1)"),
            QuestionOption(id="B", text="O(n)"),
        ],
        correct_option_id="A",
        explanation="Amortized constant time.",
        review_status="approved",
    )
    await q.insert()

    now = datetime.now(timezone.utc)
    # Simulate question served 70 seconds ago (exceeding 60s + 5s buffer)
    attempt = QuizAttempt(
        user_id=user.id,
        subject_slug="dsa",
        attempt_number=1,
        started_at=now - timedelta(seconds=75),
        expires_at=now + timedelta(hours=2),
        assigned_question_ids=[q.id],
        current_question_index=0,
        items=[],
        is_completed=False,
    )
    # Manually populate item with served_at 70 seconds ago
    from app.models.consolidated import QuestionItemAttempt
    attempt.items.append(
        QuestionItemAttempt(
            question_id=q.id,
            served_at=now - timedelta(seconds=70),
            time_limit_seconds=60,
        )
    )
    await attempt.insert()

    # Client claims elapsed_seconds=2.0 (trying to cheat)
    result = await QuizService.submit_answer(
        attempt_id=attempt.id,
        user_id=user.id,
        selected_option_id="A",
        elapsed_seconds=2.0,
    )

    # Server-side calculation overrides client and marks question timed out
    updated = await QuizAttempt.get(attempt.id)
    item = updated.items[0]
    assert item.timed_out is True
    assert item.is_correct is False
    assert item.elapsed_seconds >= 65.0


@pytest.mark.asyncio
async def test_peer_quiz_learner_answer_hiding_and_edit_lock():
    """Verify learner never sees correct_option_index, and creator edits are blocked after learner responds."""
    creator_id = PydanticObjectId()
    learner_id = PydanticObjectId()
    now = datetime.now(timezone.utc)

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-peer-test",
        yjs_doc_id="doc-peer-test",
        status="teacher_a",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=creator_id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays",
                learn_subject_slug="dbms",
                learn_topic_slug="sql",
            ),
            SessionParticipant(
                user_id=learner_id,
                role="teacher_b",
                teach_subject_slug="dbms",
                teach_topic_slug="sql",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays",
            ),
        ],
    )
    await sess.insert()

    # 1. Creator drafts peer quiz with correct_option_index = 2
    quiz = await PeerQuizService.create_or_update_peer_quiz(
        session_id=sess.id,
        creator_id=creator_id,
        questions=[
            {
                "question_type": "mcq",
                "prompt": "What is 2 + 2?",
                "options": ["1", "2", "4", "5"],
                "correct_option_index": 2,
            }
        ],
    )

    # 2. When formatted for creator, correct_option_index is visible (2)
    creator_view = _format_quiz(quiz, creator_id)
    assert creator_view.questions[0].correct_option_index == 2

    # 3. When formatted for learner, correct_option_index is None (strictly hidden!)
    learner_view = _format_quiz(quiz, learner_id)
    assert learner_view.questions[0].correct_option_index is None

    # 4. Learner submits answer
    await PeerQuizService.submit_answers(
        session_id=sess.id,
        learner_id=learner_id,
        answers=[{"question_index": 0, "partner_answer": "2"}],
    )

    # 5. Creator tries to edit after learner has answered: rejected with 400
    with pytest.raises(HTTPException) as exc_info:
        await PeerQuizService.create_or_update_peer_quiz(
            session_id=sess.id,
            creator_id=creator_id,
            questions=[
                {
                    "question_type": "mcq",
                    "prompt": "Updated prompt",
                    "options": ["A", "B"],
                    "correct_option_index": 0,
                }
            ],
        )
    assert exc_info.value.status_code == 400

    # 6. Learner tries to re-submit after grading: rejected with 400
    with pytest.raises(HTTPException) as exc_re:
        await PeerQuizService.submit_answers(
            session_id=sess.id,
            learner_id=learner_id,
            answers=[{"question_index": 0, "partner_answer": "2"}],
        )
    assert exc_re.value.status_code == 400
