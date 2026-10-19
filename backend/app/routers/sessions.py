import asyncio
import json
import logging
import os
import sys
import tempfile
import time
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


class ExecuteCodeRequest(BaseModel):
    code: str
    language: str = "python"


class PrecheckSubmitRequest(BaseModel):
    answers: Dict[str, str]  # question_id -> selected_option_id


class AdvancePhaseRequest(BaseModel):
    target_phase: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str


@router.post("/execute-code", response_model=APIResponse[dict])
async def execute_code(
    payload: ExecuteCodeRequest,
):
    """
    Executes student Python / JS code in an isolated subprocess with 6-second timeout.
    Returns real stdout, stderr, execution time, and exit code.
    """
    lang = (payload.language or "python").lower()
    code = payload.code or ""
    start_time = time.perf_counter()
    temp_path = None

    if lang in ["python", "py", "python3"]:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(process.communicate(), timeout=6.0)
                exit_code = process.returncode
                stdout_str = stdout_data.decode("utf-8", errors="replace")
                stderr_str = stderr_data.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                exit_code = 124
                stdout_str = ""
                stderr_str = "Execution Timeout: Code exceeded maximum runtime limit (6.0 seconds)."
        except Exception as e:
            exit_code = 1
            stdout_str = ""
            stderr_str = f"Execution failed: {str(e)}"
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    elif lang in ["javascript", "js", "typescript", "ts"]:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                "node",
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(process.communicate(), timeout=6.0)
                exit_code = process.returncode
                stdout_str = stdout_data.decode("utf-8", errors="replace")
                stderr_str = stderr_data.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                exit_code = 124
                stdout_str = ""
                stderr_str = "Execution Timeout: Code exceeded maximum runtime limit (6.0 seconds)."
        except Exception as e:
            exit_code = 1
            stdout_str = ""
            stderr_str = f"Execution failed: {str(e)}"
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
    else:
        exit_code = 1
        stdout_str = ""
        stderr_str = f"Unsupported language '{lang}'. Supported: python, javascript."

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

    return APIResponse(
        success=True,
        data={
            "language": lang,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "exit_code": exit_code,
            "execution_time_ms": elapsed_ms,
        },
    )


@router.get("/my", response_model=APIResponse[List[dict]])
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
):
    sessions = await SessionService.get_user_sessions(current_user.id)
    return APIResponse(success=True, data=sessions)


@router.post("/demo", response_model=APIResponse[dict])
async def create_demo_session(
    current_user: User = Depends(get_current_user),
):
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
