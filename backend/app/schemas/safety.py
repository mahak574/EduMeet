from datetime import datetime
from typing import List, Literal, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class CreateReportRequest(BaseModel):
    reported_user_id: PydanticObjectId
    session_id: Optional[PydanticObjectId] = None
    reason: Literal["harassment", "inappropriate_behavior", "no_show", "spam"]
    details: str = Field(..., min_length=10, max_length=1500)
    block_user: bool = Field(default=False, description="Automatically block reported user")


class ReportResponse(BaseModel):
    id: PydanticObjectId
    reporter_user_id: PydanticObjectId
    reported_user_id: PydanticObjectId
    session_id: Optional[PydanticObjectId] = None
    reason: str
    details: str
    status: Literal["pending", "reviewed", "dismissed", "banned"]
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime


class ResolveReportRequest(BaseModel):
    status: Literal["reviewed", "dismissed", "banned"]
    resolution_notes: Optional[str] = Field(None, max_length=1000)


class BlockUserRequest(BaseModel):
    blocked_user_id: PydanticObjectId


class BlockResponse(BaseModel):
    id: PydanticObjectId
    blocker_user_id: PydanticObjectId
    blocked_user_id: PydanticObjectId
    blocked_user_name: Optional[str] = None
    created_at: datetime
