import logging
from app.services.email_service.base import EmailProvider

logger = logging.getLogger(__name__)


class ConsoleEmailProvider(EmailProvider):
    async def send_otp(self, email: str, code: str) -> bool:
        separator = "=" * 60
        msg = (
            f"\n{separator}\n"
            f" [LOCAL DEV EMAIL DISPATCH]\n"
            f" To: {email}\n"
            f" Subject: Your EduMeet Authentication Code\n"
            f" Code: >>> {code} <<<\n"
            f" Expires: in 10 minutes\n"
            f"{separator}\n"
        )
        print(msg, flush=True)
        logger.info("ConsoleEmailProvider delivered OTP to %s: %s", email, code)
        return True
