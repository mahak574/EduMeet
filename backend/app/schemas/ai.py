from typing import List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class LessonPhaseGuide(BaseModel):
    phase_name: str
    duration_minutes: int
    objectives: List[str]
    discussion_prompts: List[str]
    checklist: List[str]


class TopicPlan(BaseModel):
    topic_name: str
    subject_slug: str
    subtopic_slug: str
    teacher_name: str
    learner_name: str
    phases: List[LessonPhaseGuide]
    starter_code_or_query: Optional[str] = None


class SessionPlanResponse(BaseModel):
    session_id: PydanticObjectId
    is_llm_generated: bool
    ai_consent_mutual: bool
    plan_teacher_a: TopicPlan
    plan_teacher_b: TopicPlan
    general_guidelines: List[str]
    notice: Optional[str] = None


class CoachExplainRequest(BaseModel):
    concept_or_question: str = Field(..., min_length=3, max_length=500)
    subject_slug: str
    topic_slug: str
    student_confusion: Optional[str] = Field(None, max_length=500)


class CoachExplainResponse(BaseModel):
    concept: str
    is_llm_generated: bool
    analogy: str
    explanation: str
    key_takeaways: List[str]
    practice_question: str
