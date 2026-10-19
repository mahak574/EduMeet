from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PoolJoinRequest(BaseModel):
    subject_slugs: List[str] = Field(default_factory=lambda: ["dsa", "dbms"])


class PoolStatusResponse(BaseModel):
    is_in_pool: bool
    subject_slugs: List[str] = Field(default_factory=list)
    entered_at: Optional[datetime] = None
    status: Optional[str] = None


class MatchPartyInfo(BaseModel):
    user_id: str
    user_name: str
    teach_subject_slug: str
    teach_topic_slug: str
    learn_subject_slug: str
    learn_topic_slug: str
    confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    selected_slot: Optional[datetime] = None


class MatchResponse(BaseModel):
    id: str
    status: str
    score: float
    common_languages: List[str]
    proposed_slots: List[datetime]
    expires_at: datetime
    session_id: Optional[str] = None
    my_teach_subject: Optional[str] = None
    my_teach_topic: Optional[str] = None
    my_learn_subject: Optional[str] = None
    my_learn_topic: Optional[str] = None
    partner_name: Optional[str] = None
    partner_id: Optional[str] = None
    has_confirmed: bool = False
    partner_has_confirmed: bool = False
    participants: List[MatchPartyInfo] = Field(default_factory=list)


class MatchConfirmRequest(BaseModel):
    chosen_slot: datetime


class MatchDeclineRequest(BaseModel):
    reason: Optional[str] = None


class MatchingCycleRunResponse(BaseModel):
    matches_created_count: int
    pool_candidates_count: int
    match_ids: List[str]
