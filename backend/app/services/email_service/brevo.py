import logging
import httpx
from app.config import settings
from app.services.email_service.base import EmailProvider

logger = logging.getLogger(__name__)


class BrevoEmailProvider(EmailProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send_otp(self, email: str, code: str) -> bool:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "sender": {
                "name": settings.APP_NAME,
                "email": settings.EMAILS_FROM_EMAIL,
            },
            "to": [
                {"email": email}
            ],
            "subject": f"{code} is your EduMeet verification code",
            "htmlContent": (
                f"<div style='font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 32px 24px; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;'>"
                f"<div style='margin-bottom: 24px; text-align: center;'>"
                f"<h1 style='color: #4F46E5; margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;'>EduMeet</h1>"
                f"<p style='color: #64748b; font-size: 14px; margin-top: 4px;'>Peer-to-Peer Learning Platform</p>"
                f"</div>"
                f"<div style='padding: 24px; background: #f8fafc; border-radius: 8px; border: 1px solid #f1f5f9; text-align: center;'>"
                f"<p style='color: #334155; font-size: 15px; margin: 0 0 16px 0;'>Here is your one-time verification code:</p>"
                f"<div style='font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #4F46E5; font-family: monospace; padding: 12px 0;'>{code}</div>"
                f"<p style='color: #64748b; font-size: 13px; margin: 16px 0 0 0;'>This code expires in 10 minutes and is single-use.</p>"
                f"</div>"
                f"<p style='color: #94a3b8; font-size: 12px; margin-top: 24px; text-align: center; line-height: 1.5;'>"
                f"If you did not request this verification code, please disregard this email.<br/>"
                f"EduMeet will never ask for your code or password."
                f"</p>"
                f"</div>"
            ),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    logger.info("Brevo successfully sent verification OTP to %s", email)
                    return True
                logger.error("Brevo API error %s: %s", resp.status_code, resp.text)
                return False
        except Exception as exc:
            logger.error("Failed to send OTP via Brevo to %s: %s", email, exc)
            return False
