from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.consolidated import PeerQuiz, User
from app.schemas.common import APIResponse
from app.schemas.peer_quiz import (
    CreatePeerQuizRequest,
    PeerQuestionResponse,
    PeerQuizResponse,
    SubmitPeerQuizAnswersRequest,
)
from app.services.peer_quiz_service import PeerQuizService

router = APIRouter(prefix="/peer-quizzes", tags=["Peer Quizzes"])


def _format_quiz(quiz: PeerQuiz) -> PeerQuizResponse:
    q_responses = [
        PeerQuestionResponse(
            question_type=q.question_type,
            prompt=q.prompt,
            options=q.options,
            correct_option_index=q.correct_option_index,
            partner_answer=q.partner_answer,
            is_auto_graded_correct=q.is_auto_graded_correct,
            partner_clarity_rating=q.partner_clarity_rating,
        )
        for q in quiz.questions
    ]
    correct_count = sum(1 for q in quiz.questions if q.is_auto_graded_correct is True)
    score_pct = round((correct_count / max(1, len(quiz.questions))) * 100.0, 1) if quiz.graded_at else None

    return PeerQuizResponse(
        id=str(quiz.id),
        session_id=str(quiz.session_id),
        creator_id=str(quiz.creator_id),
        target_learner_id=str(quiz.target_learner_id),
        subject_slug=quiz.subject_slug,
        topic_slug=quiz.topic_slug,
        questions=q_responses,
        submitted_at=quiz.submitted_at,
        graded_at=quiz.graded_at,
        score_percentage=score_pct,
    )


@router.post("/{session_id}/create", response_model=APIResponse[PeerQuizResponse])
async def create_peer_quiz(
    session_id: PydanticObjectId,
    req: CreatePeerQuizRequest,
    current_user: User = Depends(get_current_user),
):
    questions_dicts = [q.model_dump() for q in req.questions]
    quiz = await PeerQuizService.create_or_update_peer_quiz(
        session_id=session_id,
        creator_id=current_user.id,
        questions=questions_dicts,
    )
    return APIResponse(success=True, data=_format_quiz(quiz))


@router.get("/{session_id}/assigned", response_model=APIResponse[Optional[PeerQuizResponse]])
async def get_assigned_peer_quiz(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    quiz = await PeerQuizService.get_quiz_for_learner(session_id, current_user.id)
    if not quiz:
        return APIResponse(success=True, data=None)
    return APIResponse(success=True, data=_format_quiz(quiz))


@router.get("/{session_id}/drafted", response_model=APIResponse[Optional[PeerQuizResponse]])
async def get_drafted_peer_quiz(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    quiz = await PeerQuizService.get_quiz_created_by(session_id, current_user.id)
    if not quiz:
        return APIResponse(success=True, data=None)
    return APIResponse(success=True, data=_format_quiz(quiz))


@router.post("/{session_id}/submit", response_model=APIResponse[PeerQuizResponse])
async def submit_peer_quiz_answers(
    session_id: PydanticObjectId,
    req: SubmitPeerQuizAnswersRequest,
    current_user: User = Depends(get_current_user),
):
    answers_dicts = [a.model_dump() for a in req.answers]
    evaluated_quiz = await PeerQuizService.submit_answers(
        session_id=session_id,
        learner_id=current_user.id,
        answers=answers_dicts,
    )
    return APIResponse(success=True, data=_format_quiz(evaluated_quiz))
