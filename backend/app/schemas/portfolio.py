from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class BadgeResponse(BaseModel):
    badge_key: str
    title: str
    description: str
    icon_name: str
    awarded_at: datetime


class UpdatePortfolioRequest(BaseModel):
    portfolio_slug: Optional[str] = Field(None, min_length=3, max_length=40)
    portfolio_is_public: bool = True


class PublicPortfolioResponse(BaseModel):
    full_name: str
    country: str
    timezone: str
    portfolio_slug: Optional[str] = None
    is_public: bool
    is_verified_student: bool
    is_mentor: bool
    completed_sessions_count: int
    distinct_partners_count: int
    partner_diversity_unlocked: bool  # True only if distinct_partners >= 5
    teaching_subjects: List[str]
    badges: List[BadgeResponse]
    average_clarity_rating: Optional[float] = None
    average_helpfulness_rating: Optional[float] = None
    notice: Optional[str] = None
