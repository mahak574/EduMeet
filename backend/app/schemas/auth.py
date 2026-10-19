from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SendOTPRequest(BaseModel):
    email: EmailStr
    turnstile_token: str = Field(..., description="Cloudflare Turnstile verification response")


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google OAuth2 ID token")


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    age_confirmed: bool
    country: str
    timezone: str
    languages: list[str]
    subjects_studied: list[str]
    is_verified_student: bool
    is_mentor: bool
    ai_consent: bool = True
    portfolio_slug: Optional[str] = None
    portfolio_is_public: bool = False


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    user: UserResponse
