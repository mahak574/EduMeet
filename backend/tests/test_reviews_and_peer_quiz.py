from datetime import datetime, timedelta, timezone
import pytest
from beanie import PydanticObjectId

from app.models.consolidated import (
    MistakeEntry,
    PeerQuiz,
    Question,
    QuestionOption,
    ReviewSchedule,
    Session,
    SessionParticipant,
    SkillProfile,
    SkillSnapshot,
    TopicSkill,
    User,
)
from app.services.evaluation_service import EvaluationService
from app.services.peer_quiz_service import PeerQuizService
from app.services.review_service import ReviewService, apply_sm2


def test_sm2_algorithm():
    """Validates SuperMemo-2 mathematical progression and lapse resets."""
    # Day 1: First review with perfect recall (q=5)
    rep, ef, interval = apply_sm2(repetition=0, easiness_factor=2.5, interval_days=1, quality=5)
    assert rep == 1
    assert interval == 1
    assert ef == 2.6

    # Day 2: Second review with good recall (q=4)
    rep2, ef2, interval2 = apply_sm2(repetition=rep, easiness_factor=ef, interval_days=interval, quality=4)
    assert rep2 == 2
    assert interval2 == 6
    assert ef2 == 2.6

    # Day 8: Third review with perfect recall (q=5)
    rep3, ef3, interval3 = apply_sm2(repetition=rep2, easiness_factor=ef2, interval_days=interval2, quality=5)
    assert rep3 == 3
    assert interval3 == round(6 * 2.7)  # ~16 days
    assert ef3 == 2.7

    # Failure / Lapse (q=1) -> Must reset repetitions to 0 and interval to 1
    rep_lapse, ef_lapse, interval_lapse = apply_sm2(repetition=rep3, easiness_factor=ef3, interval_days=interval3, quality=1)
    assert rep_lapse == 0
    assert interval_lapse == 1
    assert ef_lapse < ef3
    assert ef_lapse >= 1.3


@pytest.mark.asyncio
async def test_mistake_journal_and_sm2_schedule():
    """Validates mistake logging and automatic spaced repetition schedule creation."""
    u_id = PydanticObjectId()
    q_id = PydanticObjectId()

    mistake = await ReviewService.log_mistake(
        user_id=u_id,
        subject_slug="dsa",
        topic_slug="trees-and-graphs",
        subtopic_slug="dfs-bfs",
        question_ref_id=q_id,
        question_prompt="What is the time complexity of BFS on an adjacency matrix?",
        mistake_tag="didnt_know_concept",
        learner_notes="Forgot matrix lookups are V^2",
    )
    assert mistake.id is not None
    assert mistake.resolved is False

    # ReviewSchedule should be automatically created for this subtopic
    schedules = await ReviewService.get_all_schedules(u_id)
    assert len(schedules) == 1
    sched = schedules[0]
    assert sched.subject_slug == "dsa"
    assert sched.subtopic_slug == "dfs-bfs"
    assert sched.repetition_number == 0

    # Mark resolved
    resolved_mistake = await ReviewService.resolve_mistake(u_id, mistake.id)
    assert resolved_mistake.resolved is True


@pytest.mark.asyncio
async def test_peer_quiz_authoring_and_submission():
    """Teacher authors 2 questions; learner answers; auto-grades and logs mistakes."""
    teacher_id = PydanticObjectId()
    learner_id = PydanticObjectId()
    now = datetime.now(timezone.utc)

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-peer",
        yjs_doc_id="doc-peer",
        status="teacher_a",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=teacher_id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            SessionParticipant(
                user_id=learner_id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    # Teacher drafts 2 MCQ questions for Learner
    quiz = await PeerQuizService.create_or_update_peer_quiz(
        session_id=sess.id,
        creator_id=teacher_id,
        questions=[
            {
                "question_type": "mcq",
                "prompt": "What is the lookup time complexity of a Hash Map on average?",
                "options": ["O(1)", "O(n)", "O(log n)"],
                "correct_option_index": 0,
            },
            {
                "question_type": "mcq",
                "prompt": "Which collision resolution technique uses linked lists?",
                "options": ["Open Addressing", "Separate Chaining", "Linear Probing"],
                "correct_option_index": 1,
            },
        ],
    )
    assert len(quiz.questions) == 2
    assert quiz.target_learner_id == learner_id

    # Learner submits: question 0 correct (0), question 1 incorrect (0 instead of 1)
    graded_quiz = await PeerQuizService.submit_answers(
        session_id=sess.id,
        learner_id=learner_id,
        answers=[
            {"question_index": 0, "partner_answer": "0", "clarity_rating": "clear"},
            {"question_index": 1, "partner_answer": "0", "clarity_rating": "confusing"},
        ],
    )
    assert graded_quiz.graded_at is not None
    assert graded_quiz.questions[0].is_auto_graded_correct is True
    assert graded_quiz.questions[1].is_auto_graded_correct is False
    assert graded_quiz.questions[1].partner_clarity_rating == "confusing"

    # Verify that the incorrect question was logged to learner's mistake journal
    mistakes = await ReviewService.get_mistakes(learner_id)
    assert len(mistakes) == 1
    assert "Separate Chaining" in mistakes[0].learner_notes or "Peer quiz" in mistakes[0].learner_notes


@pytest.mark.asyncio
async def test_postcheck_learning_gain_delta_and_profile_update():
    """Post-check computes delta against baseline and updates skill profile."""
    u_id = PydanticObjectId()
    now = datetime.now(timezone.utc)

    # Seed approved question
    q = Question(
        subject_slug="dsa",
        topic_slug="dynamic-programming",
        subtopic_slug="1d-dp",
        difficulty="hard",
        prompt_text="What is the recurrence relation for Fibonacci?",
        options=[
            QuestionOption(id="A", text="F(n) = F(n-1) + F(n-2)"),
            QuestionOption(id="B", text="F(n) = F(n-1) * F(n-2)"),
        ],
        correct_option_id="A",
        explanation="Standard definition",
        review_status="approved",
    )
    await q.insert()

    # Create pre-session baseline snapshot (50%)
    pre_snap = SkillSnapshot(
        user_id=u_id,
        subject_slug="dsa",
        topic_slug="dynamic-programming",
        score=50.0,
        source_type="pre_session",
        source_id=PydanticObjectId(),
    )
    await pre_snap.insert()

    # User profile initially at 45%
    prof = SkillProfile(
        user_id=u_id,
        subjects={
            "dsa": {
                "dynamic-programming": TopicSkill(overall_score=45.0),
            }
        },
    )
    await prof.insert()

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-postcheck",
        yjs_doc_id="doc-postcheck",
        status="followup",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=u_id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
                pre_session_snapshot_id=pre_snap.id,
            ),
            SessionParticipant(
                user_id=PydanticObjectId(),
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    # Submit post-check with correct answer (100%)
    res = await EvaluationService.submit_postcheck(
        session_id=sess.id,
        user_id=u_id,
        answers={str(q.id): "A"},
    )
    assert res["post_score_percentage"] == 100.0
    assert res["pre_score_percentage"] == 50.0
    assert res["learning_gain_delta"] == 50.0  # +50% growth!

    # Check updated profile: 45 * 0.70 + 100 * 0.30 = 31.5 + 30 = 61.5%
    updated_prof = await SkillProfile.find_one(SkillProfile.user_id == u_id)
    dp_skill = updated_prof.subjects["dsa"]["dynamic-programming"]
    assert dp_skill.score == 61.5


@pytest.mark.asyncio
async def test_session_rating_and_partner_diversity():
    """Rating updates partner stats and advances distinct partner count towards 5-partner portfolio threshold."""
    now = datetime.now(timezone.utc)
    u_rater = User(email="rater@test.com", full_name="Rater Student", age_confirmed=True, country="US")
    u_partner = User(
        email="partner@test.com",
        full_name="Partner Student",
        age_confirmed=True,
        country="US",
        completed_sessions_count=4,
        distinct_partners=[PydanticObjectId() for _ in range(4)],  # Currently 4 distinct partners
    )
    await u_rater.insert()
    await u_partner.insert()

    sess = Session(
        match_id=PydanticObjectId(),
        video_room_id="room-rate",
        yjs_doc_id="doc-rate",
        status="followup",
        scheduled_start_utc=now,
        scheduled_end_utc=now + timedelta(minutes=60),
        participants=[
            SessionParticipant(
                user_id=u_rater.id,
                role="teacher_a",
                teach_subject_slug="dsa",
                teach_topic_slug="arrays-and-hashing",
                learn_subject_slug="dsa",
                learn_topic_slug="dynamic-programming",
            ),
            SessionParticipant(
                user_id=u_partner.id,
                role="teacher_b",
                teach_subject_slug="dsa",
                teach_topic_slug="dynamic-programming",
                learn_subject_slug="dsa",
                learn_topic_slug="arrays-and-hashing",
            ),
        ],
    )
    await sess.insert()

    # Rater gives 4.5 clarity, 5.0 helpfulness
    await EvaluationService.submit_session_rating(
        session_id=sess.id,
        user_id=u_rater.id,
        clarity=4.5,
        helpfulness=5.0,
        feedback_text="Great explanation of DP base cases!",
    )

    # Check partner: completed sessions should increment to 5, distinct partners = 5, portfolio public unlocked!
    p_after = await User.get(u_partner.id)
    assert p_after.completed_sessions_count == 5
    assert len(p_after.distinct_partners) == 5
    assert p_after.portfolio_is_public is True
