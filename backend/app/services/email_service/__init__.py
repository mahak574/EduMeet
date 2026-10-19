from app.config import settings
from app.services.email_service.base import EmailProvider
from app.services.email_service.console import ConsoleEmailProvider
from app.services.email_service.resend import ResendEmailProvider
from app.services.email_service.brevo import BrevoEmailProvider
from app.services.email_service.smtp import SMTPEmailProvider


def get_email_provider() -> EmailProvider:
    if settings.EMAIL_PROVIDER == "brevo":
        if not settings.BREVO_API_KEY:
            raise RuntimeError("BREVO_API_KEY is not configured.")
        return BrevoEmailProvider(api_key=settings.BREVO_API_KEY)
    elif settings.EMAIL_PROVIDER == "resend":
        if not settings.RESEND_API_KEY:
            raise RuntimeError("RESEND_API_KEY is not configured.")
        return ResendEmailProvider(api_key=settings.RESEND_API_KEY)
    elif settings.EMAIL_PROVIDER == "smtp":
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            raise RuntimeError("SMTP_HOST and SMTP_USER must be configured when EMAIL_PROVIDER=smtp.")
        return SMTPEmailProvider(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD or "",
            from_email=settings.EMAILS_FROM_EMAIL,
        )
    # Default is console provider for development
    return ConsoleEmailProvider()
