from typing import List, Optional
from pydantic import BaseModel, Field


class StartQuizRequest(BaseModel):
    subject_slug: str = Field(..., description="Subject slug e.g. 'dsa', 'dbms', 'operating-systems', 'python', etc.")


class QuestionOptionView(BaseModel):
    id: str
    text: str


class CurrentQuestionResponse(BaseModel):
    attempt_id: str
    subject_slug: str
    current_index: int
    total_questions: int
    question_id: str
    topic_slug: str
    difficulty: str
    prompt_text: str
    code_snippet: Optional[str] = None
    options: List[QuestionOptionView]
    time_limit_seconds: int = 60
    expires_at: str
    tab_switch_count: int = 0
    is_completed: bool = False


class SubmitAnswerRequest(BaseModel):
    selected_option_id: Optional[str] = None
    elapsed_seconds: float = Field(default=0.0, ge=0.0)


class QuizAnswerResponse(BaseModel):
    is_completed: bool
    next_index: Optional[int] = None
    total_questions: Optional[int] = None
    overall_score_percentage: Optional[float] = None
    message: Optional[str] = None


class ResumeQuizResponse(BaseModel):
    resumed: bool
    resume_count: int
    message: str


class TabSwitchResponse(BaseModel):
    tab_switch_count: int
    auto_submitted_due_to_violations: bool
    message: str


class TopicScoreBreakdown(BaseModel):
    topic_slug: str
    score: float
    confidence_level: str


class QuestionReviewItem(BaseModel):
    question_id: str
    prompt_text: str
    code_snippet: Optional[str] = None
    options: List[QuestionOptionView]
    selected_option_id: Optional[str] = None
    correct_option_id: str
    is_correct: bool = False
    timed_out: bool = False
    explanation: str
    topic_slug: str
    difficulty: str


class QuizResultResponse(BaseModel):
    attempt_id: str
    subject_slug: str
    overall_score_percentage: Optional[float]
    completed_at: Optional[str]
    is_completed: bool
    auto_submitted_due_to_violations: bool
    topic_scores: List[TopicScoreBreakdown]
    total_questions: int = 0
    correct_answers_count: int = 0
    incorrect_answers_count: int = 0
    timed_out_count: int = 0
    questions_review: List[QuestionReviewItem] = Field(default_factory=list)
