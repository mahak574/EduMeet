import asyncio
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
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
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.websocket_ticket import (
    WS_CLOSE_UNAUTHORIZED,
    consume_ws_ticket,
    issue_ws_ticket,
)
from app.services.video_service import VideoProvider
from app.models.consolidated import Message, Session, User
from app.schemas.common import APIResponse
from app.services.session_service import SessionService
from app.services.ws_session_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])



@router.get("/my", response_model=APIResponse[List[dict]])
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
):
    sessions = await SessionService.get_user_sessions(current_user.id)
    return APIResponse(success=True, data=sessions)


@router.post("/demo", response_model=APIResponse[dict])
async def create_demo_session(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    try:
        session = await SessionService.create_demo_session(current_user.id)
        return APIResponse(
            success=True,
            data={
                "session_id": str(session.id),
                "status": session.status,
                "message": "Demo session created successfully.",
            },
        )
    except Exception as e:
        logger.exception("Error creating demo session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create demo session: {str(e)}",
        )


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

    if session.status in ["closed", "cancelled", "no_show_cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is {session.status}. WebSocket tickets cannot be issued.",
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


class PrecheckSubmitRequest(BaseModel):
    answers: Dict[str, str]


class AdvancePhaseRequest(BaseModel):
    target_phase: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str


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
    # Phase transitions are server-automated via BackgroundWorker. Manual override is restricted to admins in development.
    if settings.APP_ENV != "development" or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phase advance is automated by the background worker. Manual override restricted to admins in development.",
        )

    session = await SessionService.get_session(session_id)
    is_participant = any(p.user_id == current_user.id for p in session.participants)
    if not is_participant and current_user.role != "admin":
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


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/{session_id}/video-token", response_model=APIResponse[dict])
async def get_video_token(
    session_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    session = await SessionService.get_session(session_id)
    if session.status in ["closed", "cancelled", "no_show_cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is {session.status}. Video tokens cannot be issued.",
        )

    user_p = next((p for p in session.participants if p.user_id == current_user.id), None)
    if not user_p:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

    # Enforce window [start-5min, end of followup]
    now = datetime.now(timezone.utc)
    start_utc = _ensure_utc(session.scheduled_start_utc)
    end_utc = _ensure_utc(session.scheduled_end_utc)
    if start_utc and now < (start_utc - timedelta(minutes=5)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video room is not active yet. It opens 5 minutes before scheduled start.",
        )
    if end_utc and now > end_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video session window has concluded.",
        )

    room_name = session.video_room_id or f"edumeet-{secrets.token_urlsafe(16)}"
    is_moderator = user_p.role == "teacher_a"
    video_data = VideoProvider.generate_token(
        user_id=str(current_user.id),
        user_name=current_user.full_name,
        user_email=current_user.email,
        room_name=room_name,
        is_moderator=is_moderator,
    )

    return APIResponse(
        success=True,
        data={
            **video_data,
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


@router.post("/{session_id}/messages", response_model=APIResponse[dict])
async def send_session_message(
    session_id: PydanticObjectId,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
):
    session = await SessionService.get_session(session_id)
    is_part = any(p.user_id == current_user.id for p in session.participants)
    if not is_part:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

    clean_content = req.content.strip()
    if not clean_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    chat_msg = await ws_manager.handle_chat_message(str(session_id), str(current_user.id), clean_content)
    if "error" in chat_msg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=chat_msg["error"])

    await ws_manager.broadcast(str(session_id), chat_msg)
    return APIResponse(success=True, data=chat_msg)


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

    MAX_WS_MESSAGE_SIZE = 64 * 1024  # 64 KB cap

    # 4. Message reception loop
    try:
        while True:
            raw_text = await websocket.receive_text()
            if len(raw_text) > MAX_WS_MESSAGE_SIZE:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": "Message exceeds maximum allowed size (64KB).",
                    })
                )
                continue

            try:
                data = json.loads(raw_text)
            except Exception:
                continue

            event_type = data.get("type")

            if event_type == "chat":
                content = str(data.get("content", "")).strip()
                if not content:
                    continue

                # Rate-limit chat per user
                allowed = await ws_manager.check_chat_rate_limit(session_id, user_id_str)
                if not allowed:
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "message": "Chat rate limit exceeded. Please wait a few seconds before sending another message.",
                        })
                    )
                    continue

                chat_msg = await ws_manager.handle_chat_message(session_id, user_id_str, content)
                # Do not broadcast error dicts; send error directly to the sending socket
                if "error" in chat_msg:
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "message": chat_msg["error"],
                        })
                    )
                else:
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
