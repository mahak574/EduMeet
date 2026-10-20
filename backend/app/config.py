from typing import Optional, Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["development", "production", "test"] = Field(
        ...,
        description="Application environment (required: development | production | test)",
    )
    APP_NAME: str = "EduMeet"
    APP_URL: str = "http://localhost:5173"
    API_V1_PREFIX: str = "/api/v1"

    # Cryptographic keys
    SECRET_KEY: str = "dev_secret_key_change_in_production_minimum_32_chars_long_123456"
    OTP_HMAC_SECRET: str = "dev_otp_hmac_secret_key_change_in_production_1234567890"
    WS_TICKET_SECRET: str = "dev_ws_ticket_secret_key_32_characters_long_abc"

    # Database & Redis
    MONGODB_URL: str = "mongodb://localhost:27017/edumeet"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Lifetimes
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    WS_TICKET_EXPIRE_SECONDS: int = 60

    # Email provider
    EMAIL_PROVIDER: Literal["console", "resend", "smtp", "brevo"] = "console"
    RESEND_API_KEY: Optional[str] = None
    BREVO_API_KEY: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "no-reply@edumeet.org"

    # Cloudflare Turnstile
    TURNSTILE_SECRET_KEY: str = "1x0000000000000000000000000000000AA"
    TURNSTILE_SITE_KEY: str = "1x00000000000000000000AA"

    # Google OAuth
    ENABLE_GOOGLE_LOGIN: bool = True
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Video Provider
    JAAS_APP_ID: Optional[str] = None
    JAAS_API_KEY: Optional[str] = None
    JAAS_PRIVATE_KEY_PEM: Optional[str] = None

    # AI Coach & Lesson Plan (Google Gemini free tier)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    @property
    def cookie_samesite(self) -> Literal["lax", "strict", "none"]:
        return "lax" if not self.is_production else "strict"

    @model_validator(mode="after")
    def validate_production_readiness(self) -> "Settings":
        if self.ENABLE_GOOGLE_LOGIN and not self.GOOGLE_CLIENT_ID:
            raise ValueError("Configuration error: GOOGLE_CLIENT_ID is required when Google login is enabled.")

        if self.APP_ENV == "production":
            # 1. Refuse console email provider
            if self.EMAIL_PROVIDER == "console":
                raise ValueError("Production configuration error: EMAIL_PROVIDER cannot be 'console'.")
            if self.EMAIL_PROVIDER == "resend" and not self.RESEND_API_KEY:
                raise ValueError("Production configuration error: RESEND_API_KEY is required for Resend provider.")
            if self.EMAIL_PROVIDER == "brevo" and not self.BREVO_API_KEY:
                raise ValueError("Production configuration error: BREVO_API_KEY is required for Brevo provider.")

            # 2. Refuse Cloudflare Turnstile dummy test keys
            test_keys = {
                "1x0000000000000000000000000000000AA",
                "2x0000000000000000000000000000000AA",
                "3x0000000000000000000000000000000AA",
            }
            if self.TURNSTILE_SECRET_KEY in test_keys:
                raise ValueError("Production configuration error: Test TURNSTILE_SECRET_KEY cannot be used in production.")

            # 3. Refuse weak default secrets
            if "dev_" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("Production configuration error: SECRET_KEY must be a secure random 32+ char string.")
            if "dev_" in self.OTP_HMAC_SECRET or len(self.OTP_HMAC_SECRET) < 32:
                raise ValueError("Production configuration error: OTP_HMAC_SECRET must be a secure random 32+ char string.")

        return self


settings = Settings()
