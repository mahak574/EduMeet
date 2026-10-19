import logging
import httpx
from app.config import settings
from app.services.email_service.base import EmailProvider

logger = logging.getLogger(__name__)


class ResendEmailProvider(EmailProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send_otp(self, email: str, code: str) -> bool:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": settings.EMAILS_FROM_EMAIL,
            "to": [email],
            "subject": f"{code} is your EduMeet verification code",
            "html": (
                f"<div style='font-family: sans-serif; padding: 20px; color: #333;'>"
                f"<h2>Welcome to EduMeet</h2>"
                f"<p>Your 6-digit verification code is:</p>"
                f"<h1 style='font-size: 32px; letter-spacing: 4px; color: #4F46E5;'>{code}</h1>"
                f"<p>This code is single-use and will expire in 10 minutes. Do not share it with anyone.</p>"
                f"</div>"
            ),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    logger.info("Resend successfully sent OTP to %s", email)
                    return True
                logger.error("Resend error %s: %s", resp.status_code, resp.text)
                return False
        except Exception as exc:
            logger.error("Failed to send OTP via Resend to %s: %s", email, exc)
            return False
