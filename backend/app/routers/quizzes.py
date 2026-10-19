from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_current_user_optional
from app.models.consolidated import Question, QuizAttempt, SkillProfile, User
from app.schemas.common import APIResponse
from app.schemas.quiz import (
    CurrentQuestionResponse,
    QuestionOptionView,
    QuestionReviewItem,
    QuizAnswerResponse,
    QuizResultResponse,
    ResumeQuizResponse,
    StartQuizRequest,
    SubmitAnswerRequest,
    TabSwitchResponse,
    TopicScoreBreakdown,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["Diagnostic Quizzes"])


async def _resolve_student_user(current_user: Optional[User], subject_slug: str = "python") -> User:
    if current_user:
        return current_user
    user = await User.find_one(User.email == "demo_student@example.com")
    if not user:
        user = User(
            email="demo_student@example.com",
            full_name="Guest Student",
            age_confirmed=True,
            country="US",
            timezone="UTC",
            role="student",
            subjects_studied=[subject_slug],
        )
        await user.insert()
    return user


@router.post("/start", response_model=APIResponse[dict])
async def start_diagnostic_quiz(
    payload: StartQuizRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    student = await _resolve_student_user(current_user, payload.subject_slug.lower().strip())
    attempt = await QuizService.start_diagnostic(student.id, payload.subject_slug.lower().strip())
    return APIResponse(
        success=True,
        data={
            "attempt_id": str(attempt.id),
            "subject_slug": attempt.subject_slug,
            "total_questions": len(attempt.assigned_question_ids),
            "expires_at": attempt.expires_at.isoformat(),
            "message": "Diagnostic assessment started. 60-second timer per question.",
        },
    )


@router.get("/{attempt_id}/current-question", response_model=APIResponse[CurrentQuestionResponse])
async def get_current_question(
    attempt_id: PydanticObjectId,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    student = await _resolve_student_user(current_user)
    question_data = await QuizService.get_current_question(attempt_id, student.id)
    if question_data.get("is_completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already completed.",
        )
    return APIResponse(success=True, data=CurrentQuestionResponse(**question_data))


@router.post("/{attempt_id}/answer", response_model=APIResponse[QuizAnswerResponse])
async def submit_question_answer(
    attempt_id: PydanticObjectId,
    payload: SubmitAnswerRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    student = await _resolve_student_user(current_user)
    result = await QuizService.submit_answer(
        attempt_id,
        student.id,
        payload.selected_option_id,
        payload.elapsed_seconds,
    )
    return APIResponse(success=True, data=QuizAnswerResponse(**result))


@router.post("/{attempt_id}/resume", response_model=APIResponse[ResumeQuizResponse])
async def resume_quiz_attempt(
    attempt_id: PydanticObjectId,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    student = await _resolve_student_user(current_user)
    result = await QuizService.resume_attempt(attempt_id, student.id)
    return APIResponse(success=True, data=ResumeQuizResponse(**result))


@router.post("/{attempt_id}/tab-switch", response_model=APIResponse[TabSwitchResponse])
async def record_quiz_tab_switch(
    attempt_id: PydanticObjectId,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    student = await _resolve_student_user(current_user)
    result = await QuizService.record_tab_switch(attempt_id, student.id)
    return APIResponse(success=True, data=TabSwitchResponse(**result))


@router.get("/{attempt_id}/result", response_model=APIResponse[QuizResultResponse])
async def get_quiz_result(
    attempt_id: PydanticObjectId,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    student = await _resolve_student_user(current_user)
    attempt = await QuizAttempt.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

    if not attempt.is_completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt is still in progress.")

    # Get topic scores from SkillProfile
    profile = await SkillProfile.find_one(SkillProfile.user_id == current_user.id)
    topic_breakdowns: List[TopicScoreBreakdown] = []

    if profile and attempt.subject_slug in profile.subjects:
        for t_slug, t_skill in profile.subjects[attempt.subject_slug].items():
            topic_breakdowns.append(
                TopicScoreBreakdown(
                    topic_slug=t_slug,
                    score=t_skill.score,
                    confidence_level=t_skill.confidence_level,
                )
            )

    # Fetch full question details to assemble student report card
    questions = await Question.find({"_id": {"$in": attempt.assigned_question_ids}}).to_list()
    q_map = {q.id: q for q in questions}

    item_map = {item.question_id: item for item in attempt.items}

    reviews: List[QuestionReviewItem] = []
    correct_cnt = 0
    incorrect_cnt = 0
    timed_out_cnt = 0

    for q_id in attempt.assigned_question_ids:
        q = q_map.get(q_id)
        if not q:
            continue
        item = item_map.get(q_id)
        sel_opt = item.selected_option_id if item else None
        is_corr = bool(item.is_correct) if item else False
        is_to = bool(item.timed_out) if item else False

        if is_to:
            timed_out_cnt += 1
        elif is_corr:
            correct_cnt += 1
        else:
            incorrect_cnt += 1

        opt_views = [QuestionOptionView(id=o.id, text=o.text) for o in q.options]
        reviews.append(
            QuestionReviewItem(
                question_id=str(q.id),
                prompt_text=q.prompt_text,
                code_snippet=q.code_snippet,
                options=opt_views,
                selected_option_id=sel_opt,
                correct_option_id=q.correct_option_id,
                is_correct=is_corr,
                timed_out=is_to,
                explanation=q.explanation,
                topic_slug=q.topic_slug,
                difficulty=q.difficulty,
            )
        )

    return APIResponse(
        success=True,
        data=QuizResultResponse(
            attempt_id=str(attempt.id),
            subject_slug=attempt.subject_slug,
            overall_score_percentage=attempt.overall_score_percentage,
            completed_at=attempt.completed_at.isoformat() if attempt.completed_at else None,
            is_completed=attempt.is_completed,
            auto_submitted_due_to_violations=attempt.auto_submitted_due_to_violations,
            topic_scores=topic_breakdowns,
            total_questions=len(attempt.assigned_question_ids),
            correct_answers_count=correct_cnt,
            incorrect_answers_count=incorrect_cnt,
            timed_out_count=timed_out_cnt,
            questions_review=reviews,
        ),
    )


@router.get("/history", response_model=APIResponse[List[dict]])
async def get_quiz_history(
    current_user: User = Depends(get_current_user),
):
    attempts = await QuizAttempt.find(
        QuizAttempt.user_id == current_user.id,
    ).sort("-started_at").to_list()

    items = [
        {
            "attempt_id": str(att.id),
            "subject_slug": att.subject_slug,
            "attempt_number": att.attempt_number,
            "started_at": att.started_at.isoformat(),
            "completed_at": att.completed_at.isoformat() if att.completed_at else None,
            "is_completed": att.is_completed,
            "overall_score_percentage": att.overall_score_percentage,
            "auto_submitted_due_to_violations": att.auto_submitted_due_to_violations,
        }
        for att in attempts
    ]
    return APIResponse(success=True, data=items)
