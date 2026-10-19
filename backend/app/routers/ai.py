from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.models.consolidated import User
from app.schemas.ai import (
    CoachExplainRequest,
    CoachExplainResponse,
    SessionPlanResponse,
)
from app.schemas.common import APIResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Coach & Session Plans"])


@router.get("/session-plan/{session_id}", response_model=APIResponse[SessionPlanResponse])
async def get_session_plan(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    plan = await AIService.generate_session_plan(session_id, current_user)
    return APIResponse(success=True, data=plan)


@router.post("/coach/explain", response_model=APIResponse[CoachExplainResponse])
async def get_coach_explanation(
    data: CoachExplainRequest,
    current_user: User = Depends(get_current_user),
):
    explanation = await AIService.explain_concept(data, current_user)
    return APIResponse(success=True, data=explanation)
