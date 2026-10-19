import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings
from app.services.email_service.base import EmailProvider

logger = logging.getLogger(__name__)


class SMTPEmailProvider(EmailProvider):
    def __init__(self, host: str, port: int, user: str, password: str, from_email: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email

    def _send_sync(self, recipient: str, code: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{code} is your EduMeet verification code"
        msg["From"] = self.from_email
        msg["To"] = recipient

        html_body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1e293b; max-width: 500px;">
          <h2 style="color: #4f46e5; margin-bottom: 8px;">EduMeet Verification</h2>
          <p style="font-size: 14px; color: #475569;">Your 6-digit authentication code is:</p>
          <div style="background: #f1f5f9; padding: 16px; border-radius: 12px; text-align: center; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #4f46e5;">{code}</span>
          </div>
          <p style="font-size: 12px; color: #94a3b8;">This code expires in 10 minutes. Do not share it with anyone.</p>
        </div>
        """
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_email, [recipient], msg.as_string())
            logger.info("SMTP delivered OTP to %s successfully.", recipient)
            return True
        except Exception as exc:
            logger.error("Failed to send OTP via SMTP to %s: %s", recipient, exc)
            return False

    async def send_otp(self, email: str, code: str) -> bool:
        # Offload synchronous SMTP network call to async worker thread
        return await asyncio.to_thread(self._send_sync, email, code)
