from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class MistakeCreateRequest(BaseModel):
    subject_slug: str
    topic_slug: str
    subtopic_slug: str = "general"
    question_ref_id: str
    question_prompt: str
    user_mistake_tag: Literal["didnt_know_concept", "silly_mistake", "ran_out_of_time", "misunderstood_wording"] = "didnt_know_concept"
    learner_notes: Optional[str] = None


class MistakeResponse(BaseModel):
    id: str
    user_id: str
    subject_slug: str
    topic_slug: str
    subtopic_slug: str
    question_ref_id: str
    question_prompt: str
    user_mistake_tag: str
    learner_notes: Optional[str] = None
    resolved: bool
    created_at: datetime


class ReviewScheduleResponse(BaseModel):
    id: str
    user_id: str
    subject_slug: str
    subtopic_slug: str
    repetition_number: int
    easiness_factor: float
    interval_days: int
    next_review_date: datetime
    last_reviewed_at: Optional[datetime] = None
    is_due: bool = False


class EvaluateReviewRequest(BaseModel):
    quality_rating: int = Field(..., ge=0, le=5, description="0=blackout, 3=pass with effort, 5=perfect recall")


class SessionRatingRequest(BaseModel):
    clarity: float = Field(..., ge=1.0, le=5.0)
    helpfulness: float = Field(..., ge=1.0, le=5.0)
    feedback_text: Optional[str] = None


class PostCheckSubmitRequest(BaseModel):
    answers: dict  # question_id -> selected_option_id


class PostCheckResultResponse(BaseModel):
    session_id: str
    pre_score_percentage: Optional[float] = None
    post_score_percentage: float
    learning_gain_delta: float
    total_questions: int
    correct_count: int
    snapshot_id: str
