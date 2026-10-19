from datetime import datetime, timedelta, timezone
import pytest
from beanie import PydanticObjectId

from app.models.consolidated import (
    Question,
    QuestionOption,
    QuizAttempt,
    Session,
    SessionParticipant,
    SkillSnapshot,
    User,
)
from app.services.session_service import SessionService


@pytest.mark.asyncio
async def test_session_details_and_roles():
    """Validates role resolution and server-authoritative remaining time."""
    now = datetime.now(timezone.utc)
    u1_id = PydanticObjectId()
    u2_id = PydanticObjectId()

    u1 = User(email="u1@test.com", full_name="User One", age_confirmed=True, country="US")
    u2 = User(email="u2@test.com", full_name="User Two", age_confirmed=True, country="US")
    await u1.insert()
    await u2.insert()

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-123",
        yjs_doc_id="doc-123",
        status="teacher_a",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        phase_ends_at=now + timedelta(seconds=1200),
        participants=[
            SessionParticipant(
                user_id=u1.id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            SessionParticipant(
                user_id=u2.id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    details1 = await SessionService.get_session_details(sess.id, u1.id)
    assert details1["my_role"] == "teacher_a"
    assert details1["is_current_teacher"] is True
    assert details1["partner_name"] == "User Two"
    assert 1190 <= details1["remaining_seconds"] <= 1205

    details2 = await SessionService.get_session_details(sess.id, u2.id)
    assert details2["my_role"] == "teacher_b"
    assert details2["is_current_teacher"] is False


@pytest.mark.asyncio
async def test_phase_transitions_sequence():
    """Validates strict state machine progression through all phases."""
    now = datetime.now(timezone.utc)
    u1_id = PydanticObjectId()
    u2_id = PydanticObjectId()

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-trans",
        yjs_doc_id="doc-trans",
        status="waiting_room",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=u1_id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            SessionParticipant(
                user_id=u2_id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    # Step 1: waiting_room -> teacher_a
    s1 = await SessionService.advance_phase(sess.id)
    assert s1.status == "teacher_a"
    assert s1.phase_ends_at is not None
    assert s1.actual_start_utc is not None

    # Step 2: teacher_a -> teacher_b
    s2 = await SessionService.advance_phase(sess.id)
    assert s2.status == "teacher_b"

    # Step 3: teacher_b -> quiz_exchange
    s3 = await SessionService.advance_phase(sess.id)
    assert s3.status == "quiz_exchange"

    # Step 4: quiz_exchange -> followup
    s4 = await SessionService.advance_phase(sess.id)
    assert s4.status == "followup"

    # Step 5: followup -> closed
    s5 = await SessionService.advance_phase(sess.id)
    assert s5.status == "closed"
    assert s5.chat_is_locked is True
    assert s5.actual_end_utc is not None


@pytest.mark.asyncio
async def test_waiting_room_presence_auto_transition():
    """Clock starts and transitions to teacher_a only when both are present."""
    now = datetime.now(timezone.utc)
    u1_id = PydanticObjectId()
    u2_id = PydanticObjectId()

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-auto",
        yjs_doc_id="doc-auto",
        status="waiting_room",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=u1_id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            SessionParticipant(
                user_id=u2_id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    # User 1 connects -> still waiting room
    s_step1, evt1 = await SessionService.handle_user_connected(sess.id, u1_id)
    assert s_step1.status == "waiting_room"
    assert evt1 is None
    assert u1_id in s_step1.present_user_ids

    # User 2 connects -> both present -> transitions to teacher_a
    s_step2, evt2 = await SessionService.handle_user_connected(sess.id, u2_id)
    assert s_step2.status == "teacher_a"
    assert evt2 == "PHASE_TRANSITION"
    assert s_step2.phase_ends_at is not None


@pytest.mark.asyncio
async def test_disconnect_grace_and_pause_extension():
    """Disconnect pauses the session and reconnect extends the phase deadline."""
    now = datetime.now(timezone.utc)
    u1_id = PydanticObjectId()
    u2_id = PydanticObjectId()

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-pause",
        yjs_doc_id="doc-pause",
        status="teacher_a",
        present_user_ids=[u1_id, u2_id],
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        phase_ends_at=now + timedelta(seconds=1500),
        participants=[
            SessionParticipant(
                user_id=u1_id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            SessionParticipant(
                user_id=u2_id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    # User 2 drops
    sess_paused, was_paused = await SessionService.handle_user_disconnected(sess.id, u2_id)
    assert was_paused is True
    assert sess_paused.is_paused is True
    assert sess_paused.paused_at is not None

    # Simulate 5-second disconnect
    old_deadline = sess_paused.phase_ends_at
    sess_paused.paused_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    await sess_paused.save()

    # User 2 reconnects
    sess_resumed, evt = await SessionService.handle_user_connected(sess.id, u2_id)
    assert sess_resumed.is_paused is False
    assert evt == "SESSION_RESUMED"
    assert sess_resumed.total_paused_seconds >= 5
    assert sess_resumed.phase_ends_at > old_deadline


@pytest.mark.asyncio
async def test_waiting_room_precheck_flow():
    """Pre-check returns held-out items and records baseline SkillSnapshot."""
    now = datetime.now(timezone.utc)
    u_id = PydanticObjectId()

    # Seed 3 questions for arrays-and-hashing
    q_list = []
    for i in range(3):
        q = Question(
            subject_slug="dsa",
            topic_slug="arrays-and-hashing",
            subtopic_slug="hash-maps",
            difficulty="medium",
            prompt_text=f"Precheck Question {i}",
            options=[
                QuestionOption(id="A", text="Option A"),
                QuestionOption(id="B", text="Option B"),
            ],
            correct_option_id="A",
            explanation="Explanation",
            review_status="approved",
        )
        await q.insert()
        q_list.append(q)

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-precheck",
        yjs_doc_id="doc-precheck",
        status="waiting_room",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=u_id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
            SessionParticipant(
                user_id=PydanticObjectId(),
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
        ],
    )
    await sess.insert()

    # Fetch questions
    questions = await SessionService.get_precheck_questions(sess.id, u_id)
    assert len(questions) >= 3
    assert all("correct_option_id" not in q for q in questions)

    # Submit 2 correct, 1 incorrect
    answers = {
        str(q_list[0].id): "A",  # Correct
        str(q_list[1].id): "A",  # Correct
        str(q_list[2].id): "B",  # Incorrect
    }
    result = await SessionService.submit_precheck(sess.id, u_id, answers)
    assert result["score_percentage"] == 66.7
    assert result["correct_count"] == 2
    assert result["total_questions"] == 3

    # Verify baseline snapshot created
    snap = await SkillSnapshot.get(PydanticObjectId(result["snapshot_id"]))
    assert snap is not None
    assert snap.source_type == "pre_session"
    assert snap.score == 66.7


@pytest.mark.asyncio
async def test_create_demo_session():
    """Validates that create_demo_session creates a functional demo session and peer."""
    user = User(email="learner@test.com", full_name="Learner", age_confirmed=True, country="US")
    await user.insert()

    demo_session = await SessionService.create_demo_session(user.id, subject="python")
    assert demo_session is not None
    assert demo_session.status == "waiting_room"
    assert demo_session.session_mode == "regular_30_30"
    assert len(demo_session.participants) == 2
    assert any(p.user_id == user.id for p in demo_session.participants)

    # Validate details can be fetched
    details = await SessionService.get_session_details(demo_session.id, user.id)
    assert details["session_id"] == str(demo_session.id)
    assert details["partner_name"] == "Jordan (Peer Mentor)"
    assert details["remaining_seconds"] > 0

