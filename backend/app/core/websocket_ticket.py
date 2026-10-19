import json
import secrets
from typing import Optional, Dict, Any
from app.config import settings
from app.database import get_redis


# Custom WebSocket Close Codes
WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403
WS_CLOSE_TICKET_EXPIRED = 4408
WS_CLOSE_RATE_LIMITED = 4429


async def issue_ws_ticket(user_id: str, session_id: str, role: str) -> str:
    """
    Issues a single-use 60-second ticket stored in Redis.
    Used by both FastAPI WebSocket and y-websocket server.
    """
    redis = get_redis()
    ticket = secrets.token_urlsafe(32)
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
    }
    key = f"ws_ticket:{ticket}"
    await redis.setex(key, settings.WS_TICKET_EXPIRE_SECONDS, json.dumps(payload))
    return ticket


async def consume_ws_ticket(ticket: str) -> Optional[Dict[str, Any]]:
    """
    Atomically validates and deletes the ticket from Redis.
    Returns payload if valid, None if expired/non-existent/already used.
    """
    redis = get_redis()
    key = f"ws_ticket:{ticket}"
    
    # Atomic get and delete
    # Redis 6.2+ supports GETDEL, fallback to pipeline if GETDEL fails
    try:
        raw_val = await redis.execute_command("GETDEL", key)
    except Exception:
        async with redis.pipeline(transaction=True) as pipe:
            pipe.get(key)
            pipe.delete(key)
            res = await pipe.execute()
            raw_val = res[0]

    if not raw_val:
        return None

    try:
        return json.loads(raw_val)
    except Exception:
        return None
