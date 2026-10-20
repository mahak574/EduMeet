from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class PeerQuestionCreate(BaseModel):
    question_type: Literal["mcq", "short_answer"] = "mcq"
    prompt: str = Field(..., min_length=5, max_length=500)
    options: Optional[List[str]] = Field(default_factory=list, max_length=5)
    correct_option_index: Optional[int] = Field(default=0, ge=0, le=4)

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v:
            if len(v) > 5:
                raise ValueError("Maximum 5 options allowed")
            for opt in v:
                if len(opt) > 200:
                    raise ValueError("Option text cannot exceed 200 characters")
        return v


class CreatePeerQuizRequest(BaseModel):
    questions: List[PeerQuestionCreate] = Field(..., min_length=1, max_length=5)


class PeerAnswerSubmission(BaseModel):
    question_index: int = Field(..., ge=0, le=4)
    partner_answer: str = Field(..., max_length=500)
    clarity_rating: Optional[Literal["clear", "confusing"]] = "clear"


class SubmitPeerQuizAnswersRequest(BaseModel):
    answers: List[PeerAnswerSubmission] = Field(..., min_length=1, max_length=5)


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
