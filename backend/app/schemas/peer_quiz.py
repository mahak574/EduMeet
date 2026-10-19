from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PeerQuestionCreate(BaseModel):
    question_type: Literal["mcq", "short_answer"] = "mcq"
    prompt: str = Field(..., min_length=5)
    options: Optional[List[str]] = Field(default_factory=list)
    correct_option_index: Optional[int] = Field(default=0, ge=0)


class CreatePeerQuizRequest(BaseModel):
    questions: List[PeerQuestionCreate] = Field(..., min_length=1, max_length=5)


class PeerAnswerSubmission(BaseModel):
    question_index: int
    partner_answer: str
    clarity_rating: Optional[Literal["clear", "confusing"]] = "clear"


class SubmitPeerQuizAnswersRequest(BaseModel):
    answers: List[PeerAnswerSubmission]


class PeerQuestionResponse(BaseModel):
    question_type: str
    prompt: str
    options: Optional[List[str]] = None
    correct_option_index: Optional[int] = None
    partner_answer: Optional[str] = None
    is_auto_graded_correct: Optional[bool] = None
    partner_clarity_rating: Optional[str] = None


class PeerQuizResponse(BaseModel):
    id: str
    session_id: str
    creator_id: str
    target_learner_id: str
    subject_slug: str
    topic_slug: str
    questions: List[PeerQuestionResponse]
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    score_percentage: Optional[float] = None
