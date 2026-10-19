from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.core.websocket_ticket import issue_ws_ticket
from app.models.consolidated import Session, User
from app.schemas.common import APIResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/{session_id}/ws-ticket", response_model=APIResponse[dict])
async def get_websocket_ticket(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        obj_id = PydanticObjectId(session_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format.",
        )

    session = await Session.get(obj_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    # Verify user is one of the participants
    user_participant = next(
        (p for p in session.participants if p.user_id == current_user.id),
        None,
    )
    if not user_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a registered participant in this session.",
        )

    ticket = await issue_ws_ticket(
        user_id=str(current_user.id),
        session_id=str(session.id),
        role=user_participant.role,
    )

    return APIResponse(
        success=True,
        data={
            "ticket": ticket,
            "expires_in_seconds": 60,
            "session_id": str(session.id),
            "role": user_participant.role,
        },
    )
