from typing import Dict, List, Optional
from pydantic import BaseModel


class TopicSkillDetail(BaseModel):
    score: float
    confidence_level: str
    last_assessed_at: Optional[str] = None
    diagnostic_attempts_count: int = 0


class SkillSnapshotDetail(BaseModel):
    subject_slug: str
    topic_slug: str
    score: float
    source_type: str
    source_id: str
    recorded_at: str


class SkillProfileResponse(BaseModel):
    user_id: str
    # subject_slug -> topic_slug -> TopicSkillDetail
    subjects: Dict[str, Dict[str, TopicSkillDetail]]
    last_diagnostic_at: Dict[str, str]
    recent_snapshots: List[SkillSnapshotDetail]
