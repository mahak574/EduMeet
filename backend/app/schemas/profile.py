from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    age_confirmed: Optional[bool] = None
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    timezone: Optional[str] = Field(None, min_length=2, max_length=50)
    languages: Optional[List[str]] = None
    subjects_studied: Optional[List[str]] = None
    preferred_teaching_style: Optional[Literal["visual", "socratic", "example_heavy", "theoretical"]] = None
    learning_goals: Optional[List[str]] = None
    audio_only_default: Optional[bool] = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            c = v.strip().upper()
            from app.models.consolidated import ISO_3166_ALPHA_2
            if c not in ISO_3166_ALPHA_2:
                raise ValueError(f"Invalid ISO-3166-1 alpha-2 country code: '{v}'")
            return c
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            import zoneinfo
            if v.strip() not in zoneinfo.available_timezones():
                raise ValueError(f"Invalid IANA timezone: '{v}'")
            return v.strip()
        return v


class VerifyStudentRequest(BaseModel):
    institutional_email: str = Field(..., description="College / university email address")


class DataExportResponse(BaseModel):
    user_data: dict
    exported_at: str
