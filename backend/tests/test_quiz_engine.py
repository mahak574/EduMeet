import pytest
from datetime import datetime, timedelta, timezone
from beanie import PydanticObjectId
from fastapi import HTTPException

from app.models.consolidated import (
    Question,
    QuizAttempt,
    SkillProfile,
    SkillSnapshot,
    User,
)
from app.services.question_bank import seed_canonical_question_bank
from app.services.quiz_service import QuizService, DEFAULT_SHRINKAGE_M, DEFAULT_PRIOR_MU, DIFFICULTY_WEIGHTS


@pytest.mark.asyncio
async def test_seed_canonical_questions():
    count = await seed_canonical_question_bank()
    assert count >= 32
    dsa_count = await Question.find(Question.subject_slug == "dsa").count()
    dbms_count = await Question.find(Question.subject_slug == "dbms").count()
    assert dsa_count >= 16
    assert dbms_count >= 16


@pytest.mark.asyncio
async def test_diagnostic_quiz_lifecycle_and_bayesian_scoring():
    await seed_canonical_question_bank()

    user = User(
        email="test_diagnostic@edumeet.org",
        full_name="Alex River",
        role="student",
        age_confirmed=True,
        country="US",
        subjects_studied=["dsa", "dbms"],
    )
    await user.insert()

    # 1. Start Diagnostic
    attempt = await QuizService.start_diagnostic(user.id, "dsa")
    assert attempt.subject_slug == "dsa"
    assert attempt.attempt_number == 1
    assert len(attempt.assigned_question_ids) >= 15
    assert attempt.resume_count == 0
    assert attempt.max_resumes == 2
    assert attempt.expires_at > attempt.started_at

    # 2. Get Current Question
    q_data = await QuizService.get_current_question(attempt.id, user.id)
    assert q_data["current_index"] == 0
    assert q_data["subject_slug"] == "dsa"
    assert "options" in q_data
    # Correct answer must NOT be leaked in client response
    assert "correct_option_id" not in q_data

    # 3. Submit Answers for all questions (answer correctly for high score)
    for idx in range(len(attempt.assigned_question_ids)):
        curr_q = await Question.get(attempt.assigned_question_ids[idx])
        ans_resp = await QuizService.submit_answer(
            attempt_id=attempt.id,
            user_id=user.id,
            selected_option_id=curr_q.correct_option_id,
            elapsed_seconds=15.0,  # Within 60s limit
        )

    assert ans_resp["is_completed"] is True
    assert ans_resp["overall_score_percentage"] == 100.0

    # 4. Verify Bayesian Shrinkage SkillProfile Update
    profile = await SkillProfile.find_one(SkillProfile.user_id == user.id)
    assert profile is not None
    assert "dsa" in profile.subjects
    assert len(profile.subjects["dsa"]) == 4  # All 4 topics scored

    # Check a topic's Bayesian shrinkage formula
    # S = 100 * (sum(w_i * y_i) + m * mu) / (sum(w_i) + m)
    for topic_slug, skill in profile.subjects["dsa"].items():
        assert 50.0 <= skill.score <= 100.0  # Shrunk from 100% towards 50% prior
        assert skill.diagnostic_attempts_count == 1

    # Verify SkillSnapshot records
    snapshots = await SkillSnapshot.find(
        SkillSnapshot.user_id == user.id,
        SkillSnapshot.source_type == "diagnostic",
    ).to_list()
    assert len(snapshots) == 4


@pytest.mark.asyncio
async def test_quiz_resumption_controls():
    await seed_canonical_question_bank()

    user = User(
        email="resume_tester@edumeet.org",
        full_name="Jordan Case",
        role="student",
        age_confirmed=True,
        country="CA",
    )
    await user.insert()

    attempt = await QuizService.start_diagnostic(user.id, "dbms")

    # Resume 1: Fresh 60s timer granted
    res1 = await QuizService.resume_attempt(attempt.id, user.id)
    assert res1["resume_count"] == 1
    assert "Fresh 60-second timer" in res1["message"]

    # Resume 2: Times out current question and advances
    initial_idx = attempt.current_question_index
    res2 = await QuizService.resume_attempt(attempt.id, user.id)
    assert res2["resume_count"] == 2
    updated_attempt = await QuizAttempt.get(attempt.id)
    assert updated_attempt.current_question_index == initial_idx + 1

    # Resume 3: Must be rejected with 400
    with pytest.raises(HTTPException) as exc_info:
        await QuizService.resume_attempt(attempt.id, user.id)
    assert exc_info.value.status_code == 400
    assert "Maximum resume attempts" in exc_info.value.detail


@pytest.mark.asyncio
async def test_anti_cheat_tab_switch_violations():
    await seed_canonical_question_bank()

    user = User(
        email="anti_cheat@edumeet.org",
        full_name="Sam Fisher",
        role="student",
        age_confirmed=True,
        country="US",
    )
    await user.insert()

    attempt = await QuizService.start_diagnostic(user.id, "dsa")

    # Switches 1 to 3: warnings recorded
    for i in range(1, 4):
        tab_resp = await QuizService.record_tab_switch(attempt.id, user.id)
        assert tab_resp["tab_switch_count"] == i
        assert tab_resp["auto_submitted_due_to_violations"] is False

    # Switch 4: Auto-submits attempt and flags violations
    tab_resp4 = await QuizService.record_tab_switch(attempt.id, user.id)
    assert tab_resp4["tab_switch_count"] == 4
    assert tab_resp4["auto_submitted_due_to_violations"] is True

    # Confirm attempt is completed and marked with violations
    final_att = await QuizAttempt.get(attempt.id)
    assert final_att.is_completed is True
    assert final_att.auto_submitted_due_to_violations is True


@pytest.mark.asyncio
async def test_attempt_quota_and_cooldown_enforcement():
    await seed_canonical_question_bank()

    user = User(
        email="quota_tester@edumeet.org",
        full_name="Taylor Swift",
        role="student",
        age_confirmed=True,
        country="GB",
    )
    await user.insert()

    # Complete Attempt 1
    att1 = await QuizService.start_diagnostic(user.id, "dsa")
    att1.is_completed = True
    att1.completed_at = datetime.now(timezone.utc)
    await att1.save()

    # Retaking within 7-day cooldown must fail
    can_start, reason = await QuizService.can_start_diagnostic(user.id, "dsa")
    assert can_start is False
    assert "Cooldown active" in reason

    # Simulate cooldown expiry (completed 8 days ago)
    att1.completed_at = datetime.now(timezone.utc) - timedelta(days=8)
    await att1.save()

    # Now Attempt 2 can start
    can_start, _ = await QuizService.can_start_diagnostic(user.id, "dsa")
    assert can_start is True
    att2 = await QuizService.start_diagnostic(user.id, "dsa")
    att2.is_completed = True
    att2.completed_at = datetime.now(timezone.utc) - timedelta(days=8)
    await att2.save()

    # Attempt 3
    att3 = await QuizService.start_diagnostic(user.id, "dsa")
    att3.is_completed = True
    att3.completed_at = datetime.now(timezone.utc) - timedelta(days=8)
    await att3.save()

    # Attempt 4 should fail due to 3-attempt limit
    can_start, reason = await QuizService.can_start_diagnostic(user.id, "dsa")
    assert can_start is False
    assert "maximum limit of 3 diagnostic attempts" in reason
