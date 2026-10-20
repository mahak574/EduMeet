import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


class VideoProvider:
    """
    Issues authenticated RS256 JaaS JWTs.
    Public meet.jit.si fallback is strictly prohibited.
    """

    @classmethod
    def is_configured(cls) -> bool:
        return bool(settings.JAAS_APP_ID and settings.JAAS_API_KEY and settings.JAAS_PRIVATE_KEY_PEM)

    @classmethod
    def generate_token(
        cls,
        user_id: str,
        user_name: str,
        user_email: Optional[str],
        room_name: str,
        is_moderator: bool = False,
    ) -> Dict[str, Any]:
        if not cls.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Video service is not configured. Public Jitsi fallbacks are strictly prohibited.",
            )

        now = datetime.now(timezone.utc)
        clean_pem = settings.JAAS_PRIVATE_KEY_PEM.strip()
        # Handle cases where newlines were escaped as literal \n in env strings
        if "\\n" in clean_pem and "\n" not in clean_pem:
            clean_pem = clean_pem.replace("\\n", "\n")

        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": settings.JAAS_API_KEY,
        }

        # Exact room claim format for JaaS: either bare room_name or AppID/room_name
        # Exact room claim (wildcard '*' strictly disallowed)
        clean_room = room_name.strip()
        full_room_name = f"{settings.JAAS_APP_ID}/{clean_room}"

        payload = {
            "aud": "jitsi",
            "iss": "chat",
            "sub": settings.JAAS_APP_ID,
            "room": clean_room,
            "iat": int(now.timestamp()),
            "nbf": int((now - timedelta(seconds=10)).timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),  # 15-minute token expiry
            "context": {
                "user": {
                    "id": str(user_id),
                    "name": user_name,
                    "email": user_email or f"{user_id}@edumeet.org",
                    "avatar": "",
                    "moderator": is_moderator,
                },
                "features": {
                    "livestreaming": False,
                    "recording": False,
                    "transcription": False,
                    "outbound-call": False,
                },
            },
        }

        token = jwt.encode(payload, clean_pem, algorithm="RS256", headers=headers)
        return {
            "token": token,
            "room_name": full_room_name,
            "domain": "8x8.vc",
            "expires_in_seconds": 900,
        }
