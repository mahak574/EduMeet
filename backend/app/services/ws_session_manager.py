import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Any
from beanie import PydanticObjectId
from fastapi import WebSocket

from app.models.consolidated import Message, User
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)


class SessionConnectionManager:
    def __init__(self):
        # Maps session_id (str) -> dict of { user_id (str): WebSocket }
        self.active_rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, session_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_rooms:
            self.active_rooms[session_id] = {}
        self.active_rooms[session_id][user_id] = websocket
        logger.info("User %s connected to session %s WS (room size: %d)", user_id, session_id, len(self.active_rooms[session_id]))

    def disconnect(self, session_id: str, user_id: str):
        if session_id in self.active_rooms:
            if user_id in self.active_rooms[session_id]:
                del self.active_rooms[session_id][user_id]
            if len(self.active_rooms[session_id]) == 0:
                del self.active_rooms[session_id]
        logger.info("User %s disconnected from session %s WS", user_id, session_id)

    async def broadcast(self, session_id: str, message: Dict[str, Any], exclude_user_id: str = None):
        if session_id not in self.active_rooms:
            return

        dead_connections = []
        payload_str = json.dumps(message)

        for uid, ws in self.active_rooms[session_id].items():
            if exclude_user_id and uid == exclude_user_id:
                continue
            try:
                await ws.send_text(payload_str)
            except Exception as e:
                logger.warning("Error broadcasting to user %s in session %s: %s", uid, session_id, e)
                dead_connections.append(uid)

        # Clean up dead sockets
        for uid in dead_connections:
            self.disconnect(session_id, uid)

    async def handle_chat_message(
        self, session_id: str, sender_id: str, content: str
    ) -> Dict[str, Any]:
        """Persists chat message to MongoDB and returns broadcast event."""
        sender_user = await User.get(PydanticObjectId(sender_id))
        sender_name = sender_user.full_name if sender_user else "Student"

        # Check if chat is locked on session
        session = await SessionService.get_session(PydanticObjectId(session_id))
        if session.chat_is_locked:
            return {"error": "Chat is locked for this session."}

        msg_doc = Message(
            session_id=PydanticObjectId(session_id),
            sender_id=PydanticObjectId(sender_id),
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        await msg_doc.insert()

        return {
            "type": "chat",
            "message_id": str(msg_doc.id),
            "sender_id": sender_id,
            "sender_name": sender_name,
            "content": content,
            "created_at": msg_doc.created_at.isoformat(),
        }


# Singleton manager instance
ws_manager = SessionConnectionManager()
