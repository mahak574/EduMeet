from typing import List, Literal, Optional
from pydantic import BaseModel, Field


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


class VerifyStudentRequest(BaseModel):
    institutional_email: str = Field(..., description="College / university email address")


class DataExportResponse(BaseModel):
    user_data: dict
    exported_at: str
