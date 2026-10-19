import pytest
from datetime import datetime, timezone
from beanie import PydanticObjectId

from app.models.consolidated import (
    Badge,
    PeerQuiz,
    Session,
    SessionParticipant,
    User,
)
from app.schemas.ai import CoachExplainRequest
from app.services.ai_service import AIService
from app.services.badge_service import BadgeService


@pytest.mark.asyncio
async def test_ai_session_plan_respects_consent_fallback():
    user_a = User(
        email="student.a@school.edu",
        full_name="Alice Student",
        age_confirmed=True,
        country="IN",
        timezone="Asia/Kolkata",
        ai_consent=True,
    )
    await user_a.insert()

    user_b = User(
        email="student.b@school.edu",
        full_name="Bob Learner",
        age_confirmed=True,
        country="IN",
        timezone="Asia/Kolkata",
        ai_consent=False,  # Bob opts OUT of AI processing
    )
    await user_b.insert()

    session = Session(
        match_id=PydanticObjectId(),
        scheduled_start_utc=datetime.now(timezone.utc),
        scheduled_end_utc=datetime.now(timezone.utc),
        video_room_id="edumeet-test-room-phase6",
        yjs_doc_id="yjs-test-doc-phase6",
        participants=[
            SessionParticipant(
                user_id=user_a.id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dbms",
                learn_topic_slug="relational-schema-and-sql",
            ),
            SessionParticipant(
                user_id=user_b.id,
                role="teacher_b",
                teach_subject_slug="dbms",
                teach_topic_slug="relational-schema-and-sql",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
        status="waiting_room",
    )
    await session.insert()

    # Generate plan
    plan_resp = await AIService.generate_session_plan(session.id, user_a)

    # Must fall back deterministically because mutual AI consent is False
    assert plan_resp.is_llm_generated is False
    assert plan_resp.ai_consent_mutual is False
    assert "deterministic" in plan_resp.notice.lower()
    assert plan_resp.plan_teacher_a.subtopic_slug == "arrays-and-hashing"
    assert len(plan_resp.plan_teacher_a.phases) == 3
    assert plan_resp.plan_teacher_b.subtopic_slug == "relational-schema-and-sql"


@pytest.mark.asyncio
async def test_ai_coach_explain_fallback():
    user = User(
        email="socratic.learner@school.edu",
        full_name="Charlie Reader",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        ai_consent=False,
    )
    await user.insert()

    explanation = await AIService.explain_concept(
        CoachExplainRequest(
            concept_or_question="Two-Phase Locking (2PL)",
            subject_slug="dbms",
            topic_slug="concurrency-and-recovery",
            student_confusion="Why can't we release locks during growing phase?",
        ),
        user,
    )

    assert explanation.is_llm_generated is False
    assert len(explanation.analogy) > 10
    assert len(explanation.key_takeaways) == 3
    assert "practice_question" in explanation.model_dump()


@pytest.mark.asyncio
async def test_portfolio_badges_and_partner_diversity():
    user = User(
        email="scholar@university.edu",
        full_name="Deepa Scholar",
        age_confirmed=True,
        country="IN",
        timezone="Asia/Kolkata",
        portfolio_slug="deepa-teach",
        portfolio_is_public=True,
        completed_sessions_count=1,
        distinct_partners=[PydanticObjectId()],
    )
    await user.insert()

    # Milestone with 1 completed session
    awarded = await BadgeService.evaluate_user_milestones(user.id)
    badge_keys = [b.badge_key for b in awarded]
    assert "first_session" in badge_keys
    assert "five_partners" not in badge_keys

    # Now add 4 more distinct partners (total 5)
    user.completed_sessions_count = 5
    user.distinct_partners = [PydanticObjectId() for _ in range(5)]
    await user.save()

    awarded_second = await BadgeService.evaluate_user_milestones(user.id)
    all_badges = await BadgeService.get_user_badges(user.id)
    all_keys = [b.badge_key for b in all_badges]
    assert "five_partners" in all_keys
