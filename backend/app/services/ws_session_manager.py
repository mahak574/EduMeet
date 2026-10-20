import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from beanie import PydanticObjectId
from fastapi import WebSocket

from app.database import get_redis
from app.models.consolidated import Message, User
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)


class SessionConnectionManager:
    def __init__(self):
        # Maps session_id (str) -> dict of { user_id (str): WebSocket }
        self.active_rooms: Dict[str, Dict[str, WebSocket]] = {}
        # PubSub listener tasks per session_id
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
        # In-memory rate limiting fallback: user_key -> list of float timestamps
        self.user_msg_times: Dict[str, List[float]] = {}

    async def connect(self, session_id: str, user_id: str, websocket: WebSocket):
        # If user is already connected on an old socket, close it
        if session_id in self.active_rooms and user_id in self.active_rooms[session_id]:
            old_ws = self.active_rooms[session_id][user_id]
            try:
                logger.info("Closing previous WebSocket for user %s on reconnect to session %s", user_id, session_id)
                await old_ws.close(code=1000, reason="Replaced by new connection")
            except Exception as e:
                logger.debug("Failed closing previous WebSocket: %s", e)

        await websocket.accept()
        if session_id not in self.active_rooms:
            self.active_rooms[session_id] = {}
        self.active_rooms[session_id][user_id] = websocket

        # Start Redis pub/sub listener for this room if not already running
        if session_id not in self.pubsub_tasks:
            self.pubsub_tasks[session_id] = asyncio.create_task(self._listen_to_redis_channel(session_id))

        logger.info(
            "User %s connected to session %s WS (room size: %d)",
            user_id,
            session_id,
            len(self.active_rooms[session_id]),
        )

    def disconnect(self, session_id: str, user_id: str):
        if session_id in self.active_rooms:
            if user_id in self.active_rooms[session_id]:
                del self.active_rooms[session_id][user_id]
            if len(self.active_rooms[session_id]) == 0:
                del self.active_rooms[session_id]
                if session_id in self.pubsub_tasks:
                    task = self.pubsub_tasks.pop(session_id)
                    task.cancel()
        logger.info("User %s disconnected from session %s WS", user_id, session_id)

    async def _listen_to_redis_channel(self, session_id: str):
        """Listens to Redis pub/sub channel for room broadcast events."""
        channel_name = f"ws:room:{session_id}"
        redis = get_redis()
        if not redis or not hasattr(redis, "pubsub"):
            return

        try:
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name)
            while True:
                raw_message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if raw_message and raw_message.get("type") == "message":
                    data_str = raw_message.get("data")
                    if isinstance(data_str, bytes):
                        data_str = data_str.decode("utf-8")
                    if data_str:
                        try:
                            payload = json.loads(data_str)
                            msg = payload.get("message")
                            exc_uid = payload.get("exclude_user_id")
                            if msg:
                                await self._local_broadcast(session_id, msg, exclude_user_id=exc_uid)
                        except Exception as parse_err:
                            logger.warning("Error parsing pubsub payload: %s", parse_err)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
            except Exception:
                pass
        except Exception as e:
            logger.warning("Redis pub/sub listener error on %s: %s", channel_name, e)

    async def _local_broadcast(
        self, session_id: str, message: Dict[str, Any], exclude_user_id: Optional[str] = None
    ):
        if session_id not in self.active_rooms:
            return

        dead_connections = []
        payload_str = json.dumps(message)

        for uid, ws in list(self.active_rooms[session_id].items()):
            if exclude_user_id and uid == exclude_user_id:
                continue
            try:
                await ws.send_text(payload_str)
            except Exception as e:
                logger.warning("Error broadcasting to user %s in session %s: %s", uid, session_id, e)
                dead_connections.append(uid)

        for uid in dead_connections:
            self.disconnect(session_id, uid)

    async def broadcast(
        self, session_id: str, message: Dict[str, Any], exclude_user_id: Optional[str] = None
    ):
        """
        Broadcasts message to room via Redis pub/sub if available, falling back to local broadcast.
        """
        redis = get_redis()
        channel_name = f"ws:room:{session_id}"
        if redis and hasattr(redis, "publish"):
            try:
                wrapper = {
                    "message": message,
                    "exclude_user_id": exclude_user_id,
                }
                await redis.publish(channel_name, json.dumps(wrapper))
                return
            except Exception as pub_err:
                logger.warning("Redis publish failed on %s: %s. Falling back to local broadcast.", channel_name, pub_err)

        await self._local_broadcast(session_id, message, exclude_user_id)

    async def check_chat_rate_limit(self, session_id: str, user_id: str) -> bool:
        """
        Rate limits chat messages per user (max 5 messages per 5 seconds).
        """
        redis = get_redis()
        key = f"ws_ratelimit:{session_id}:{user_id}"
        if redis and hasattr(redis, "incr"):
            try:
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, 5)
                return count <= 5
            except Exception:
                pass

        # In-memory sliding window fallback
        now = time.time()
        times = self.user_msg_times.get(key, [])
        times = [t for t in times if now - t < 5.0]
        if len(times) >= 5:
            self.user_msg_times[key] = times
            return False
        times.append(now)
        self.user_msg_times[key] = times
        return True

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
