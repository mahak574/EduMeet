import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from beanie import PydanticObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel
from app.config import settings
from app.core.dependencies import get_current_user
from app.core.websocket_ticket import (
    WS_CLOSE_UNAUTHORIZED,
    consume_ws_ticket,
    issue_ws_ticket,
)
from app.models.consolidated import Message, Session, User
from app.schemas.common import APIResponse
from app.services.session_service import SessionService
from app.services.ws_session_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class PrecheckSubmitRequest(BaseModel):
    answers: Dict[str, str]  # question_id -> selected_option_id


class AdvancePhaseRequest(BaseModel):
    target_phase: Optional[str] = None


@router.get("/{session_id}", response_model=APIResponse[dict])
async def get_session_details(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    details = await SessionService.get_session_details(session_id, current_user.id)
    return APIResponse(success=True, data=details)


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


@router.get("/{session_id}/precheck", response_model=APIResponse[List[dict]])
async def get_precheck_questions(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    questions = await SessionService.get_precheck_questions(session_id, current_user.id)
    return APIResponse(success=True, data=questions)


@router.post("/{session_id}/precheck/submit", response_model=APIResponse[dict])
async def submit_precheck(
    session_id: PydanticObjectId,
    req: PrecheckSubmitRequest,
    current_user: User = Depends(get_current_user),
):
    result = await SessionService.submit_precheck(session_id, current_user.id, req.answers)
    return APIResponse(success=True, data=result)


@router.post("/{session_id}/advance", response_model=APIResponse[dict])
async def advance_session_phase(
    session_id: PydanticObjectId,
    req: AdvancePhaseRequest,
    current_user: User = Depends(get_current_user),
):
    session = await SessionService.get_session(session_id)
    is_participant = any(p.user_id == current_user.id for p in session.participants)
    if not is_participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

    updated_session = await SessionService.advance_phase(session_id, req.target_phase)
    # Broadcast phase change over WebSocket
    await ws_manager.broadcast(
        str(session_id),
        {
            "type": "PHASE_TRANSITION",
            "status": updated_session.status,
            "phase_ends_at": updated_session.phase_ends_at.isoformat() if updated_session.phase_ends_at else None,
        },
    )
    return APIResponse(
        success=True,
        data={
            "session_id": str(updated_session.id),
            "status": updated_session.status,
            "phase_ends_at": updated_session.phase_ends_at,
        },
    )


@router.get("/{session_id}/video-token", response_model=APIResponse[dict])
async def get_video_token(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    session = await SessionService.get_session(session_id)
    user_p = next((p for p in session.participants if p.user_id == current_user.id), None)
    if not user_p:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

    # Generate JaaS / Jitsi Room Parameters
    room_name = session.video_room_id or f"edumeet-{session.id}"
    domain = "8x8.vc" if settings.JAAS_APP_ID else "meet.jit.si"

    return APIResponse(
        success=True,
        data={
            "room_name": room_name,
            "domain": domain,
            "display_name": current_user.full_name,
            "user_id": str(current_user.id),
            "role": user_p.role,
            "audio_only": current_user.preferences.audio_only_default,
        },
    )


@router.get("/{session_id}/messages", response_model=APIResponse[List[dict]])
async def get_session_messages(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    session = await SessionService.get_session(session_id)
    is_part = any(p.user_id == current_user.id for p in session.participants)
    if not is_part:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

    msgs = await Message.find(Message.session_id == session_id).sort("created_at").to_list()
    users = await User.find({"_id": {"$in": [m.sender_id for m in msgs]}}).to_list()
    user_name_map = {u.id: u.full_name for u in users}

    formatted = [
        {
            "id": str(m.id),
            "sender_id": str(m.sender_id),
            "sender_name": user_name_map.get(m.sender_id, "Student"),
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]
    return APIResponse(success=True, data=formatted)


@router.websocket("/ws/{session_id}")
async def session_websocket(
    websocket: WebSocket,
    session_id: str,
    ticket: str = Query(...),
):
    # 1. Ticket validation
    payload = await consume_ws_ticket(ticket)
    if not payload or payload.get("session_id") != session_id:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return

    user_id_str = payload["user_id"]
    try:
        session_obj_id = PydanticObjectId(session_id)
        user_obj_id = PydanticObjectId(user_id_str)
    except Exception:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return

    # 2. Connect
    await ws_manager.connect(session_id, user_id_str, websocket)
    session, event = await SessionService.handle_user_connected(session_obj_id, user_obj_id)

    # 3. Broadcast connection presence
    await ws_manager.broadcast(
        session_id,
        {
            "type": "presence",
            "user_id": user_id_str,
            "status": "joined",
            "present_user_ids": [str(uid) for uid in session.present_user_ids],
            "session_status": session.status,
            "phase_ends_at": session.phase_ends_at.isoformat() if session.phase_ends_at else None,
        },
    )

    if event:
        await ws_manager.broadcast(
            session_id,
            {
                "type": event,
                "status": session.status,
                "phase_ends_at": session.phase_ends_at.isoformat() if session.phase_ends_at else None,
            },
        )

    # 4. Message reception loop
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                continue

            event_type = data.get("type")

            if event_type == "chat":
                content = str(data.get("content", "")).strip()
                if content:
                    chat_msg = await ws_manager.handle_chat_message(session_id, user_id_str, content)
                    await ws_manager.broadcast(session_id, chat_msg)

            elif event_type in ["code_sync", "whiteboard_sync", "peer_quiz_sync"]:
                # Relay collaboration sync to partner
                await ws_manager.broadcast(
                    session_id,
                    {
                        "type": event_type,
                        "sender_id": user_id_str,
                        "payload": data.get("payload"),
                    },
                    exclude_user_id=user_id_str,
                )

            elif event_type == "ping":
                curr_sess = await Session.get(session_obj_id)
                rem = 0
                if curr_sess and curr_sess.phase_ends_at:
                    now_utc = datetime.now(timezone.utc)
                    rem = max(0, int((curr_sess.phase_ends_at - now_utc).total_seconds()))
                await websocket.send_text(
                    json.dumps({
                        "type": "pong",
                        "status": curr_sess.status if curr_sess else "closed",
                        "remaining_seconds": rem,
                        "is_paused": curr_sess.is_paused if curr_sess else False,
                    })
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, user_id_str)
        session, was_paused = await SessionService.handle_user_disconnected(session_obj_id, user_obj_id)
        await ws_manager.broadcast(
            session_id,
            {
                "type": "presence",
                "user_id": user_id_str,
                "status": "left",
                "is_paused": was_paused,
                "present_user_ids": [str(uid) for uid in session.present_user_ids],
            },
        )
