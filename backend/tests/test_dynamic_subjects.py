import pytest
from datetime import datetime, timezone
from beanie import PydanticObjectId

from app.models.consolidated import (
    Question,
    QuizAttempt,
    SkillProfile,
    TopicSkill,
    User,
)
from app.services.ai_question_generator import AIQuestionGenerator
from app.services.matching_service import MatchingService
from app.services.quiz_service import QuizService


@pytest.mark.asyncio
async def test_dynamic_question_generation_and_single_subject_quiz():
    """Test 1: User with 1 single subject ('python') gets dynamic questions and Bayesian scoring."""
    user = User(
        email="pythoneer@university.edu",
        full_name="Guido Learner",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        subjects_studied=["python"],
    )
    await user.insert()

    # 1. Start diagnostic for 'python'
    attempt = await QuizService.start_diagnostic(user.id, "python")
    assert attempt.subject_slug == "python"
    assert len(attempt.assigned_question_ids) >= 12  # 3-4 questions per topic across 4 topics

    # Verify questions exist in database and were dynamically generated
    python_qs = await Question.find(Question.subject_slug == "python").to_list()
    assert len(python_qs) >= 12
    topics = set(q.topic_slug for q in python_qs)
    assert len(topics) == 4

    # 2. Answer questions (alternate correct/incorrect)
    for i in range(len(attempt.assigned_question_ids)):
        q_data = await QuizService.get_current_question(attempt.id, user.id)
        if q_data.get("is_completed"):
            break

        q_obj = await Question.get(PydanticObjectId(q_data["question_id"]))
        # Submit correct for first 2, incorrect for others
        selected_opt = q_obj.correct_option_id if i < 8 else "Z"
        res = await QuizService.submit_answer(attempt.id, user.id, selected_opt, elapsed_seconds=20.0)

    # 3. Verify SkillProfile is populated only for 'python'
    profile = await SkillProfile.find_one(SkillProfile.user_id == user.id)
    assert profile is not None
    assert "python" in profile.subjects
    assert len(profile.subjects["python"]) == 4

    # 4. Verify proficiency classification: >= 70% is proficient, < 70% is learning_target
    for topic_slug, topic_skill in profile.subjects["python"].items():
        classification = QuizService.get_topic_classification(topic_skill.score)
        if topic_skill.score >= 70.0:
            assert classification == "proficient"
        else:
            assert classification == "learning_target"

    # Confirm other subjects are completely untouched
    assert "dsa" not in profile.subjects
    assert "dbms" not in profile.subjects


@pytest.mark.asyncio
async def test_two_subjects_independent_skill_storage():
    """Test 2: User with 2 subjects ('dsa', 'dbms') has independent skill storage without cross-bleed."""
    user = User(
        email="double.major@university.edu",
        full_name="Double Major",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        subjects_studied=["dsa", "dbms"],
    )
    await user.insert()

    # Create profile with high score in DSA and low score in DBMS
    profile = SkillProfile(
        user_id=user.id,
        subjects={
            "dsa": {
                "arrays-and-hashing": TopicSkill(overall_score=85.0),
                "dynamic-programming": TopicSkill(overall_score=78.0),
            },
            "dbms": {
                "transactions-and-acid": TopicSkill(overall_score=42.0),
            },
        },
    )
    await profile.insert()

    refreshed = await SkillProfile.find_one(SkillProfile.user_id == user.id)
    # Check DSA proficiency
    assert refreshed.subjects["dsa"]["arrays-and-hashing"].score == 85.0
    assert QuizService.get_topic_classification(refreshed.subjects["dsa"]["arrays-and-hashing"].score) == "proficient"

    # Check DBMS learning target
    assert refreshed.subjects["dbms"]["transactions-and-acid"].score == 42.0
    assert QuizService.get_topic_classification(refreshed.subjects["dbms"]["transactions-and-acid"].score) == "learning_target"

    # Confirm independence: updating DSA does not alter DBMS
    refreshed.subjects["dsa"]["arrays-and-hashing"].overall_score = 90.0
    await refreshed.save()

    after_update = await SkillProfile.find_one(SkillProfile.user_id == user.id)
    assert after_update.subjects["dsa"]["arrays-and-hashing"].score == 90.0
    assert after_update.subjects["dbms"]["transactions-and-acid"].score == 42.0


@pytest.mark.asyncio
async def test_five_subjects_profile_tracking():
    """Test 3: User with 5 distinct subjects tracks all 5 subjects independently."""
    five_subjects = ["dsa", "dbms", "operating-systems", "computer-networks", "system-design"]
    user = User(
        email="polymath@university.edu",
        full_name="Polymath Scholar",
        age_confirmed=True,
        country="IN",
        timezone="Asia/Kolkata",
        subjects_studied=five_subjects,
    )
    await user.insert()

    profile_dict = {}
    for subj in five_subjects:
        topics = AIQuestionGenerator.get_topics_for_subject(subj)
        profile_dict[subj] = {
            topics[0]: TopicSkill(overall_score=75.0),
            topics[1]: TopicSkill(overall_score=55.0),
        }

    profile = SkillProfile(user_id=user.id, subjects=profile_dict)
    await profile.insert()

    loaded = await SkillProfile.find_one(SkillProfile.user_id == user.id)
    assert len(loaded.subjects) == 5
    for subj in five_subjects:
        assert subj in loaded.subjects
        topics = list(loaded.subjects[subj].keys())
        assert len(topics) == 2
        # Check that high score is proficient and low score is learning target
        assert QuizService.get_topic_classification(loaded.subjects[subj][topics[0]].score) == "proficient"
        assert QuizService.get_topic_classification(loaded.subjects[subj][topics[1]].score) == "learning_target"


@pytest.mark.asyncio
async def test_arbitrary_custom_subject_assessment():
    """Test 4: User enters arbitrary custom subject ('quantum-computing') and system auto-generates content."""
    user = User(
        email="quantum@tech.edu",
        full_name="Quantum Researcher",
        age_confirmed=True,
        country="UK",
        timezone="Europe/London",
        subjects_studied=["quantum-computing"],
    )
    await user.insert()

    # Start diagnostic for non-predefined subject
    attempt = await QuizService.start_diagnostic(user.id, "quantum-computing")
    assert attempt.subject_slug == "quantum-computing"

    # Verify questions generated
    qs = await Question.find(Question.subject_slug == "quantum-computing").to_list()
    assert len(qs) >= 12
    for q in qs:
        assert q.review_status == "approved"
        assert len(q.options) == 4
        assert q.correct_option_id in ["A", "B", "C", "D"]


@pytest.mark.asyncio
async def test_dynamic_multi_subject_peer_matching():
    """Test 5: Peer matching finds optimal topic pair across multiple subjects."""
    # User A: Strong in operating-systems (process-and-threads), weak in python (functions-and-generators)
    prof_a = SkillProfile(
        user_id=PydanticObjectId(),
        subjects={
            "operating-systems": {
                "process-and-threads": TopicSkill(overall_score=85.0),  # Can teach
            },
            "python": {
                "functions-and-generators": TopicSkill(overall_score=40.0),  # Can learn
            },
        },
    )

    # User B: Strong in python (functions-and-generators), weak in operating-systems (process-and-threads)
    prof_b = SkillProfile(
        user_id=PydanticObjectId(),
        subjects={
            "python": {
                "functions-and-generators": TopicSkill(overall_score=90.0),  # Can teach
            },
            "operating-systems": {
                "process-and-threads": TopicSkill(overall_score=35.0),  # Can learn
            },
        },
    )

    pair = MatchingService.find_optimal_topic_pair(
        prof_a, prof_b, ["operating-systems", "python"]
    )
    assert pair is not None
    subj_a, topic_a, subj_b, topic_b, gain = pair
    assert gain > 0.0
    assert (subj_a == "operating-systems" and subj_b == "python") or (subj_a == "python" and subj_b == "operating-systems")


@pytest.mark.asyncio
async def test_math_curriculum_and_practical_questions():
    """Validates that mathematical subjects generate genuine practical calculations and not CS templates."""
    # 1. Test General Maths
    topics = await AIQuestionGenerator.ensure_questions_for_subject("maths", target_per_topic=2)
    assert len(topics) == 4
    math_qs = await Question.find(Question.subject_slug == "maths").to_list()
    assert len(math_qs) >= 8

    # Verify that prompts contain real math terms and NO CS template jargon
    cs_jargon = ["operational invariants", "space complexity", "window minimize", "global locks"]
    for q in math_qs:
        assert not any(jargon in q.prompt_text.lower() for jargon in cs_jargon)

    # 2. Test Commerce / CA Mathematics
    ca_topics = await AIQuestionGenerator.ensure_questions_for_subject("maths-commerce-ca", target_per_topic=2)
    assert len(ca_topics) == 4
    ca_qs = await Question.find(Question.subject_slug == "maths-commerce-ca").to_list()
    assert len(ca_qs) >= 8
    # Must have practical financial calculations
    assert any("annuity" in q.prompt_text.lower() or "interest" in q.prompt_text.lower() or "revenue" in q.prompt_text.lower() for q in ca_qs)

    # 3. Test Class 11-12 Mathematics
    h_topics = await AIQuestionGenerator.ensure_questions_for_subject("maths-class-11-12", target_per_topic=2)
    assert len(h_topics) == 4
    h_qs = await Question.find(Question.subject_slug == "maths-class-11-12").to_list()
    assert len(h_qs) >= 8
    assert any("derivative" in q.prompt_text.lower() or "integral" in q.prompt_text.lower() or "determinant" in q.prompt_text.lower() for q in h_qs)

