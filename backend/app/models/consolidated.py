import re
import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Literal, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from pymongo import ASCENDING, IndexModel

ISO_3166_ALPHA_2 = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
    "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS",
    "BT", "BV", "BW", "BY", "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE",
    "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF",
    "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT", "JE", "JM",
    "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC",
    "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ", "NA",
    "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG",
    "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS",
    "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO",
    "TR", "TT", "TV", "TW", "TZ", "UA", "UG", "UK", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW"
}

# ==============================================================================
# Helper Validators & Types
# ==============================================================================
SLUG_REGEX = re.compile(r"^[a-z0-9_-]+$")

def validate_slug(value: str) -> str:
    cleaned = value.strip().lower()
    if not SLUG_REGEX.match(cleaned):
        raise ValueError(f"Value '{value}' must be a valid lowercase slug matching '^[a-z0-9_-]+$' (no dots or special characters).")
    return cleaned


# ==============================================================================
# 1. User & Identity
# ==============================================================================
class UserPreferences(BaseModel):
    preferred_teaching_style: Literal["visual", "socratic", "example_heavy", "theoretical"] = "example_heavy"
    learning_goals: List[str] = Field(default_factory=list, description="e.g. ['placements', 'semester_exam']")
    audio_only_default: bool = False


class User(Document):
    email: EmailStr
    full_name: str
    role: Literal["student", "admin"] = "student"
    age_confirmed: bool = Field(..., description="Must confirm age 18+ at registration")
    country: str = Field(..., min_length=2, max_length=2, description="ISO-3166-1 alpha-2")
    timezone: str = Field(default="UTC", description="IANA timezone name e.g. 'Asia/Kolkata', 'America/New_York'")
    languages: List[str] = Field(default_factory=lambda: ["en"])
    subjects_studied: List[str] = Field(default_factory=list)
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    # Verification & Badges
    is_verified_student: bool = False
    institutional_email: Optional[EmailStr] = None
    is_mentor: bool = False
    mentor_since: Optional[datetime] = None

    # AI Consent & Privacy (Mutual consent required for LLM calls)
    ai_consent: bool = False
    ai_consent_record: Dict[str, Any] = Field(
        default_factory=lambda: {
            "consented": False,
            "consented_at": None,
            "policy_version": "1.0",
        }
    )
    ai_consent_withdrawn_at: Optional[datetime] = None

    # Teaching Portfolio (Revocable slug, public after 5+ distinct partners)
    portfolio_slug: Optional[str] = None
    portfolio_is_public: bool = False

    # Reliability & Attendance History (Used for matching weight)
    no_show_count: int = Field(default=0, ge=0)
    completed_sessions_count: int = Field(default=0, ge=0)
    distinct_partners: List[PydanticObjectId] = Field(default_factory=list)

    # Pilot Research Study
    pilot_group: Optional[Literal["treatment", "waitlist"]] = None

    # Status & Audit
    is_active: bool = True
    is_blocked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("country", mode="after")
    @classmethod
    def validate_country(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in ISO_3166_ALPHA_2:
            raise ValueError(f"Invalid ISO-3166-1 alpha-2 country code: '{v}'")
        return v_upper

    @field_validator("timezone", mode="after")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in zoneinfo.available_timezones():
            raise ValueError(f"Invalid IANA timezone: '{v}'")
        return v

    @field_validator("subjects_studied", mode="after")
    @classmethod
    def validate_subjects(cls, subjects: List[str]) -> List[str]:
        return [validate_slug(s) for s in subjects]

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("institutional_email", ASCENDING)], sparse=True),
            IndexModel([("country", ASCENDING), ("languages", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
        ]


# ==============================================================================
# 2. OTP Challenge (Pre-signup & Login Verification)
# ==============================================================================
class OTPChallenge(Document):
    email: EmailStr
    hashed_otp: str = Field(..., description="HMAC-SHA256(secret_key, email + ':' + code)")
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3)
    is_used: bool = False
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "otp_challenges"
        indexes = [
            IndexModel([("email", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),  # Auto-purge expired challenges
        ]


# ==============================================================================
# 3. Skill Profile & Snapshots
# ==============================================================================
class SubtopicScore(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    attempts_count: int = 0
    last_evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TopicSkill(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    subtopics: Dict[str, SubtopicScore] = Field(default_factory=dict)
    confidence_level: str = "low"
    last_assessed_at: Optional[datetime] = None
    diagnostic_attempts_count: int = 0

    @property
    def score(self) -> float:
        return self.overall_score


class SkillProfile(Document):
    user_id: PydanticObjectId
    # Mapping: subject_slug -> topic_slug -> TopicSkill
    subjects: Dict[str, Dict[str, TopicSkill]] = Field(default_factory=dict)
    last_diagnostic_at: Dict[str, datetime] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "skill_profiles"
        indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True),
        ]


class SkillSnapshot(Document):
    user_id: PydanticObjectId
    subject_slug: str
    topic_slug: str
    score: float = Field(..., ge=0.0, le=100.0)
    source_type: Literal["diagnostic", "pre_session", "post_session"]
    source_id: PydanticObjectId
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("subject_slug", "topic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "skill_snapshots"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("subject_slug", ASCENDING), ("recorded_at", ASCENDING)]),
            IndexModel([("source_id", ASCENDING)]),
        ]


# ==============================================================================
# 4. Question Bank
# ==============================================================================
class QuestionOption(BaseModel):
    id: str = Field(..., description="'A', 'B', 'C', 'D'")
    text: str


class Question(Document):
    subject_slug: str
    topic_slug: str
    subtopic_slug: str
    difficulty: Literal["easy", "medium", "hard"]
    prompt_text: str
    code_snippet: Optional[str] = None
    options: List[QuestionOption] = Field(..., min_length=2, max_length=5)
    correct_option_id: str
    explanation: str

    # Review lifecycle
    is_ai_generated: bool = False
    review_status: Literal["approved", "pending", "rejected"] = "pending"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    repeat_exposure: bool = False  # Set to True on post-exhaustion re-serve; excluded from scoring weight
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("subject_slug", "topic_slug", "subtopic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "questions"
        indexes = [
            IndexModel([
                ("subject_slug", ASCENDING),
                ("topic_slug", ASCENDING),
                ("subtopic_slug", ASCENDING),
                ("review_status", ASCENDING)
            ]),
            IndexModel([("review_status", ASCENDING)]),
        ]


# ==============================================================================
# 5. Diagnostic Quiz Attempts
# ==============================================================================
class QuestionItemAttempt(BaseModel):
    question_id: PydanticObjectId
    served_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_limit_seconds: int = 90
    selected_option_id: Optional[str] = None
    is_correct: Optional[bool] = None
    timed_out: bool = False
    elapsed_seconds: Optional[float] = None


class QuizAttempt(Document):
    user_id: PydanticObjectId
    subject_slug: str
    attempt_number: int = Field(..., ge=1, le=3)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    is_completed: bool = False

    assigned_question_ids: List[PydanticObjectId]
    served_question_ids: List[PydanticObjectId] = Field(default_factory=list)
    current_question_index: int = 0
    items: List[QuestionItemAttempt] = Field(default_factory=list)

    # Expiry and Resume Management (Max 2 resumes)
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=2))
    resume_count: int = Field(default=0, ge=0)
    max_resumes: int = 2

    tab_switch_count: int = 0
    auto_submitted_due_to_violations: bool = False
    overall_score_percentage: Optional[float] = None

    @property
    def score_percentage(self) -> float:
        if self.overall_score_percentage is not None:
            return float(self.overall_score_percentage)
        correct_count = sum(1 for it in self.items if it.is_correct is True)
        total_count = len(self.items) or len(self.assigned_question_ids) or 1
        return round((correct_count / total_count) * 100, 1) if self.is_completed else 0.0

    @field_validator("subject_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "quiz_attempts"
        indexes = [
            IndexModel([
                ("user_id", ASCENDING),
                ("subject_slug", ASCENDING),
                ("attempt_number", ASCENDING)
            ], unique=True),
            IndexModel([("user_id", ASCENDING), ("started_at", ASCENDING)]),
        ]


# ==============================================================================
# 6. Matches
# ==============================================================================
class MatchParty(BaseModel):
    user_id: PydanticObjectId
    teach_subject_slug: str
    teach_topic_slug: str
    learn_subject_slug: str
    learn_topic_slug: str
    confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    selected_slot: Optional[datetime] = None

    @field_validator("teach_subject_slug", "teach_topic_slug", "learn_subject_slug", "learn_topic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)


class Match(Document):
    # Match.participants must be exactly 2 for strict 1:1 in MVP
    participants: List[MatchParty] = Field(..., min_length=2, max_length=2)
    score: float = Field(..., description="Computed edge weight")
    common_languages: List[str]
    proposed_slots: List[datetime]
    status: Literal["pending", "confirmed", "expired", "rejected"] = "pending"
    session_id: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    class Settings:
        name = "matches"
        indexes = [
            IndexModel([("status", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)]),
            IndexModel([("session_id", ASCENDING)]),
        ]


class MatchingPoolEntry(Document):
    user_id: PydanticObjectId
    subject_slugs: List[str] = Field(default_factory=list)
    status: Literal["active", "matched", "cancelled"] = "active"
    entered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_match_id: Optional[PydanticObjectId] = None

    class Settings:
        name = "matching_pool"
        indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING), ("entered_at", ASCENDING)]),
        ]


# ==============================================================================
# 7. Availability
# ==============================================================================
class RecurringLocalSlot(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_min: int = Field(..., ge=0, le=1439, description="Start minute since midnight [0, 1439]")
    end_min: int = Field(..., ge=1, le=1440, description="End minute since midnight [1, 1440], half-open [start_min, end_min)")

    @model_validator(mode="after")
    def validate_interval(self) -> "RecurringLocalSlot":
        if self.start_min >= self.end_min:
            raise ValueError(f"start_min ({self.start_min}) must be strictly less than end_min ({self.end_min})")
        return self

    @property
    def start_time_str(self) -> str:
        return f"{self.start_min // 60:02d}:{self.start_min % 60:02d}"

    @property
    def end_time_str(self) -> str:
        return f"{self.end_min // 60:02d}:{self.end_min % 60:02d}"


class Availability(Document):
    user_id: PydanticObjectId
    timezone: str = Field(default="UTC", description="IANA timezone e.g. 'America/New_York'")
    weekly_slots: List[RecurringLocalSlot] = Field(default_factory=list)
    specific_blocked_dates: List[str] = Field(default_factory=list, description="YYYY-MM-DD local dates")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "availability"
        indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True),
        ]


# ==============================================================================
# 8. Sessions (No TTL Index; Persistent Audit Trail)
# ==============================================================================
class SessionParticipant(BaseModel):
    user_id: PydanticObjectId
    role: Literal["teacher_a", "teacher_b"]
    teach_subject_slug: str
    teach_topic_slug: str
    learn_subject_slug: str
    learn_topic_slug: str
    pre_session_snapshot_id: Optional[PydanticObjectId] = None
    post_session_snapshot_id: Optional[PydanticObjectId] = None
    rating_given: Optional[Dict[str, float]] = None
    feedback_text: Optional[str] = None


class Session(Document):
    match_id: Optional[PydanticObjectId] = None
    session_mode: Literal["regular_30_30", "instant_help", "mock_interview", "silent_costudy", "project_buddy"] = "regular_30_30"
    status: Literal[
        "scheduled",
        "waiting_room",
        "teacher_a",
        "teacher_b",
        "quiz_exchange",
        "followup",
        "closed",
        "cancelled",
        "no_show_cancelled",
    ] = "scheduled"

    # Attendance in waiting room (atomic transition filter: present_user_ids: {"$all": [A, B]})
    present_user_ids: List[PydanticObjectId] = Field(default_factory=list)

    # Disconnect grace & pause tracking (3 min disconnect grace, 10 min total pause cap)
    disconnect_grace_seconds: int = 180
    total_paused_seconds: int = 0
    max_pause_cap_seconds: int = 600
    is_paused: bool = False
    paused_at: Optional[datetime] = None

    scheduled_start_utc: datetime
    scheduled_end_utc: datetime
    actual_start_utc: Optional[datetime] = None
    actual_end_utc: Optional[datetime] = None

    # Server Authoritative Timer Controls
    phase_ends_at: Optional[datetime] = None

    # Room identifiers (never store JWTs in DB)
    video_room_id: str
    yjs_doc_id: str
    participants: List[SessionParticipant] = Field(..., min_length=2, max_length=2)

    # Chat retention & audit
    chat_is_locked: bool = False
    chat_locked_at: Optional[datetime] = None
    ai_processing_consented: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sessions"
        # Removed all TTL indexes from sessions
        indexes = [
            IndexModel([("scheduled_start_utc", ASCENDING)]),
            IndexModel([("status", ASCENDING), ("phase_ends_at", ASCENDING)]),
        ]


# ==============================================================================
# 9. Messages (30-day Retention via Scheduled Purge, No 1-hour TTL)
# ==============================================================================
class Message(Document):
    session_id: PydanticObjectId
    sender_id: PydanticObjectId
    content: str
    original_language: str = "en"
    translations: Dict[str, str] = Field(default_factory=dict)
    seen_by: List[PydanticObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_flagged_for_investigation: bool = False  # If True, scheduled purge skips until report closed

    class Settings:
        name = "messages"
        # Removed expires_at 1-hour TTL index; messages are retained for 30 days & purged via worker
        indexes = [
            IndexModel([("session_id", ASCENDING), ("created_at", ASCENDING)]),
            IndexModel([("created_at", ASCENDING), ("is_flagged_for_investigation", ASCENDING)]),
        ]


# ==============================================================================
# 10. Peer Quizzes
# ==============================================================================
class PeerQuestion(BaseModel):
    question_type: Literal["mcq", "short_answer"]
    prompt: str
    options: Optional[List[str]] = None
    correct_option_index: Optional[int] = None
    partner_answer: Optional[str] = None
    is_auto_graded_correct: Optional[bool] = None
    partner_clarity_rating: Optional[Literal["clear", "confusing"]] = None
    ai_quality_flag: Optional[Literal["valid", "trivial", "wrong"]] = None


class PeerQuiz(Document):
    session_id: PydanticObjectId
    creator_id: PydanticObjectId
    target_learner_id: PydanticObjectId
    subject_slug: str
    topic_slug: str
    questions: List[PeerQuestion] = Field(..., min_length=1, max_length=5)
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None

    @field_validator("subject_slug", "topic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "peer_quizzes"
        indexes = [
            IndexModel([("session_id", ASCENDING), ("creator_id", ASCENDING)]),
        ]


# ==============================================================================
# 11. Mistake Journal
# ==============================================================================
class MistakeEntry(Document):
    user_id: PydanticObjectId
    subject_slug: str
    topic_slug: str
    subtopic_slug: str
    question_ref_id: PydanticObjectId
    question_prompt: str
    user_mistake_tag: Literal["didnt_know_concept", "silly_mistake", "ran_out_of_time", "misunderstood_wording"]
    learner_notes: Optional[str] = None
    resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("subject_slug", "topic_slug", "subtopic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "mistake_entries"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("subject_slug", ASCENDING), ("resolved", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
        ]


# ==============================================================================
# 12. Spaced Repetition (SM-2)
# ==============================================================================
class ReviewSchedule(Document):
    user_id: PydanticObjectId
    subject_slug: str
    subtopic_slug: str
    repetition_number: int = Field(default=0, ge=0)
    easiness_factor: float = Field(default=2.5, ge=1.3)
    interval_days: int = Field(default=1)
    next_review_date: datetime
    last_reviewed_at: Optional[datetime] = None

    @field_validator("subject_slug", "subtopic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "review_schedule"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("next_review_date", ASCENDING)]),
        ]


# ==============================================================================
# 13. Badges
# ==============================================================================
class Badge(Document):
    user_id: PydanticObjectId
    badge_key: str
    title: str
    description: str
    icon_name: str
    awarded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "badges"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("badge_key", ASCENDING)]),
        ]


# ==============================================================================
# 14. Moderation & Safety Reports
# ==============================================================================
class Report(Document):
    reporter_user_id: PydanticObjectId
    reported_user_id: PydanticObjectId
    session_id: Optional[PydanticObjectId] = None
    reason: Literal["harassment", "inappropriate_behavior", "no_show", "spam"]
    details: str
    status: Literal["pending", "reviewed", "dismissed", "banned"] = "pending"
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "reports"
        indexes = [
            IndexModel([("status", ASCENDING)]),
            IndexModel([("reported_user_id", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
        ]


# ==============================================================================
# 15. Blocks (Pairing Mutual Exclusion)
# ==============================================================================
class Block(Document):
    blocker_user_id: PydanticObjectId
    blocked_user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "blocks"
        indexes = [
            IndexModel([("blocker_user_id", ASCENDING), ("blocked_user_id", ASCENDING)], unique=True),
            IndexModel([("blocked_user_id", ASCENDING)]),
        ]


# ==============================================================================
# 16. Web Push Subscriptions
# ==============================================================================
class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscription(Document):
    user_id: PydanticObjectId
    endpoint: str
    keys: PushKeys
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "push_subscriptions"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("endpoint", ASCENDING)], unique=True),
        ]


# ==============================================================================
# 17. Session Notes
# ==============================================================================
class TopicKeyTakeaway(BaseModel):
    topic: str
    key_points: List[str]
    suggested_review: List[str]


class SessionNotes(Document):
    session_id: PydanticObjectId
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    takeaways: List[TopicKeyTakeaway] = Field(default_factory=list)
    recap_card_url: Optional[str] = None

    class Settings:
        name = "session_notes"
        indexes = [
            IndexModel([("session_id", ASCENDING)], unique=True),
        ]


# ==============================================================================
# 18. Instant Help Queue
# ==============================================================================
class InstantHelpRequest(Document):
    requester_id: PydanticObjectId
    subject_slug: str
    topic_slug: str
    description: str
    status: Literal["queued", "paired", "cancelled", "expired"] = "queued"
    paired_session_id: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    @field_validator("subject_slug", "topic_slug", mode="after")
    @classmethod
    def validate_slugs(cls, val: str) -> str:
        return validate_slug(val)

    class Settings:
        name = "instant_help_requests"
        indexes = [
            IndexModel([("status", ASCENDING), ("subject_slug", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ]


# ==============================================================================
# 19. Telemetry Events (Audit & Research; No Raw Chat or Quiz Answers)
# ==============================================================================
class TelemetryEvent(Document):
    user_id: PydanticObjectId
    event_name: str
    # Payload strictly contains operational metrics/ids; NEVER raw chat text or quiz answers
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "telemetry_events"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("timestamp", ASCENDING)]),
            IndexModel([("event_name", ASCENDING), ("timestamp", ASCENDING)]),
        ]
