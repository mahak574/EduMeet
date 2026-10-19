from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_user
from app.models.consolidated import MistakeEntry, ReviewSchedule, User
from app.schemas.common import APIResponse
from app.schemas.reviews import (
    EvaluateReviewRequest,
    MistakeCreateRequest,
    MistakeResponse,
    PostCheckResultResponse,
    PostCheckSubmitRequest,
    ReviewScheduleResponse,
    SessionRatingRequest,
)
from app.services.evaluation_service import EvaluationService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews & Spaced Repetition"])


@router.post("/mistakes", response_model=APIResponse[MistakeResponse])
async def log_mistake(
    req: MistakeCreateRequest,
    current_user: User = Depends(get_current_user),
):
    entry = await ReviewService.log_mistake(
        user_id=current_user.id,
        subject_slug=req.subject_slug,
        topic_slug=req.topic_slug,
        subtopic_slug=req.subtopic_slug,
        question_ref_id=PydanticObjectId(req.question_ref_id),
        question_prompt=req.question_prompt,
        mistake_tag=req.user_mistake_tag,
        learner_notes=req.learner_notes,
    )
    return APIResponse(
        success=True,
        data=MistakeResponse(
            id=str(entry.id),
            user_id=str(entry.user_id),
            subject_slug=entry.subject_slug,
            topic_slug=entry.topic_slug,
            subtopic_slug=entry.subtopic_slug,
            question_ref_id=str(entry.question_ref_id),
            question_prompt=entry.question_prompt,
            user_mistake_tag=entry.user_mistake_tag,
            learner_notes=entry.learner_notes,
            resolved=entry.resolved,
            created_at=entry.created_at,
        ),
    )


@router.get("/mistakes", response_model=APIResponse[List[MistakeResponse]])
async def get_mistakes(
    subject_slug: Optional[str] = None,
    resolved: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
):
    entries = await ReviewService.get_mistakes(current_user.id, subject_slug, resolved)
    return APIResponse(
        success=True,
        data=[
            MistakeResponse(
                id=str(e.id),
                user_id=str(e.user_id),
                subject_slug=e.subject_slug,
                topic_slug=e.topic_slug,
                subtopic_slug=e.subtopic_slug,
                question_ref_id=str(e.question_ref_id),
                question_prompt=e.question_prompt,
                user_mistake_tag=e.user_mistake_tag,
                learner_notes=e.learner_notes,
                resolved=e.resolved,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )


@router.patch("/mistakes/{mistake_id}/resolve", response_model=APIResponse[MistakeResponse])
async def resolve_mistake(
    mistake_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    entry = await ReviewService.resolve_mistake(current_user.id, mistake_id)
    return APIResponse(
        success=True,
        data=MistakeResponse(
            id=str(entry.id),
            user_id=str(entry.user_id),
            subject_slug=entry.subject_slug,
            topic_slug=entry.topic_slug,
            subtopic_slug=entry.subtopic_slug,
            question_ref_id=str(entry.question_ref_id),
            question_prompt=entry.question_prompt,
            user_mistake_tag=entry.user_mistake_tag,
            learner_notes=entry.learner_notes,
            resolved=entry.resolved,
            created_at=entry.created_at,
        ),
    )


@router.get("/schedules/due", response_model=APIResponse[List[ReviewScheduleResponse]])
async def get_due_review_schedules(
    current_user: User = Depends(get_current_user),
):
    schedules = await ReviewService.get_due_reviews(current_user.id)
    return APIResponse(
        success=True,
        data=[
            ReviewScheduleResponse(
                id=str(s.id),
                user_id=str(s.user_id),
                subject_slug=s.subject_slug,
                subtopic_slug=s.subtopic_slug,
                repetition_number=s.repetition_number,
                easiness_factor=s.easiness_factor,
                interval_days=s.interval_days,
                next_review_date=s.next_review_date,
                last_reviewed_at=s.last_reviewed_at,
                is_due=True,
            )
            for s in schedules
        ],
    )


@router.get("/schedules", response_model=APIResponse[List[ReviewScheduleResponse]])
async def get_all_review_schedules(
    current_user: User = Depends(get_current_user),
):
    schedules = await ReviewService.get_all_schedules(current_user.id)
    return APIResponse(
        success=True,
        data=[
            ReviewScheduleResponse(
                id=str(s.id),
                user_id=str(s.user_id),
                subject_slug=s.subject_slug,
                subtopic_slug=s.subtopic_slug,
                repetition_number=s.repetition_number,
                easiness_factor=s.easiness_factor,
                interval_days=s.interval_days,
                next_review_date=s.next_review_date,
                last_reviewed_at=s.last_reviewed_at,
                is_due=s.next_review_date <= s.last_reviewed_at if s.last_reviewed_at else True,
            )
            for s in schedules
        ],
    )


@router.post("/schedules/{schedule_id}/evaluate", response_model=APIResponse[ReviewScheduleResponse])
async def evaluate_review_schedule(
    schedule_id: PydanticObjectId,
    req: EvaluateReviewRequest,
    current_user: User = Depends(get_current_user),
):
    schedule = await ReviewService.evaluate_review(
        user_id=current_user.id,
        schedule_id=schedule_id,
        quality_rating=req.quality_rating,
    )
    return APIResponse(
        success=True,
        data=ReviewScheduleResponse(
            id=str(schedule.id),
            user_id=str(schedule.user_id),
            subject_slug=schedule.subject_slug,
            subtopic_slug=schedule.subtopic_slug,
            repetition_number=schedule.repetition_number,
            easiness_factor=schedule.easiness_factor,
            interval_days=schedule.interval_days,
            next_review_date=schedule.next_review_date,
            last_reviewed_at=schedule.last_reviewed_at,
            is_due=False,
        ),
    )


@router.get("/sessions/{session_id}/postcheck", response_model=APIResponse[List[dict]])
async def get_postcheck_questions(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    qs = await EvaluationService.get_postcheck_questions(session_id, current_user.id)
    return APIResponse(success=True, data=qs)


@router.post("/sessions/{session_id}/postcheck/submit", response_model=APIResponse[PostCheckResultResponse])
async def submit_postcheck(
    session_id: PydanticObjectId,
    req: PostCheckSubmitRequest,
    current_user: User = Depends(get_current_user),
):
    res = await EvaluationService.submit_postcheck(session_id, current_user.id, req.answers)
    return APIResponse(
        success=True,
        data=PostCheckResultResponse(
            session_id=res["session_id"],
            pre_score_percentage=res["pre_score_percentage"],
            post_score_percentage=res["post_score_percentage"],
            learning_gain_delta=res["learning_gain_delta"],
            total_questions=res["total_questions"],
            correct_count=res["correct_count"],
            snapshot_id=res["snapshot_id"],
        ),
    )


@router.post("/sessions/{session_id}/rate", response_model=APIResponse[dict])
async def submit_session_rating(
    session_id: PydanticObjectId,
    req: SessionRatingRequest,
    current_user: User = Depends(get_current_user),
):
    session = await EvaluationService.submit_session_rating(
        session_id=session_id,
        user_id=current_user.id,
        clarity=req.clarity,
        helpfulness=req.helpfulness,
        feedback_text=req.feedback_text,
    )
    return APIResponse(
        success=True,
        data={
            "session_id": str(session.id),
            "rated": True,
            "clarity": req.clarity,
            "helpfulness": req.helpfulness,
        },
    )
