import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile_token(token: str, remote_ip: Optional[str] = None) -> bool:
    """
    Verifies Cloudflare Turnstile token.
    In development mode, test tokens (starting with 'XXXX.' or matching test patterns) pass automatically.
    """
    if settings.APP_ENV == "development":
        # Always allow Cloudflare standard test tokens or dummy tokens in development
        if token in {"1x00000000000000000000AA", "dummy_turnstile_token", "test_turnstile_token"} or token.startswith("XXXX."):
            logger.info("Development mode: Turnstile test token accepted.")
            return True

    if not token:
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "secret": settings.TURNSTILE_SECRET_KEY,
                "response": token,
            }
            if remote_ip:
                payload["remoteip"] = remote_ip

            response = await client.post(TURNSTILE_VERIFY_URL, data=payload)
            data = response.json()
            success = data.get("success", False)
            if not success:
                logger.warning("Turnstile verification failed: %s", data.get("error-codes"))
            return bool(success)
    except Exception as exc:
        logger.error("Exception verifying Turnstile token: %s", exc)
        return False
