import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.core.dependencies import get_current_user
from app.models.consolidated import (
    Availability,
    Block,
    MatchingPoolEntry,
    Message,
    MistakeEntry,
    OTPChallenge,
    PeerQuiz,
    PushSubscription,
    QuizAttempt,
    Report,
    ReviewSchedule,
    Session,
    SkillProfile,
    SkillSnapshot,
    TelemetryEvent,
    User,
    validate_slug,
)
from app.schemas.auth import UserResponse
from app.schemas.common import APIResponse
from app.schemas.portfolio import (
    BadgeResponse,
    PublicPortfolioResponse,
    UpdatePortfolioRequest,
)
from app.schemas.profile import DataExportResponse, UpdateProfileRequest, VerifyStudentRequest
from app.services.badge_service import BadgeService
from app.services.streak_service import StreakService

router = APIRouter(prefix="/users", tags=["Users"])


def _format_user_resp(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        age_confirmed=user.age_confirmed,
        country=user.country,
        timezone=user.timezone,
        languages=user.languages,
        subjects_studied=user.subjects_studied,
        is_verified_student=user.is_verified_student,
        is_mentor=user.is_mentor,
        ai_consent=user.ai_consent,
        portfolio_slug=user.portfolio_slug,
        portfolio_is_public=user.portfolio_is_public,
    )


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return APIResponse(success=True, data=_format_user_resp(current_user))


@router.get("/me/activity", response_model=APIResponse[dict])
async def get_my_activity_heatmap(current_user: User = Depends(get_current_user)):
    data = await StreakService.get_user_activity_heat_map(current_user.id)
    return APIResponse(success=True, data=data)


@router.patch("/me", response_model=APIResponse[UserResponse])
async def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.age_confirmed is not None:
        current_user.age_confirmed = payload.age_confirmed
    if payload.country is not None:
        c = payload.country.upper().strip()
        from app.models.consolidated import ISO_3166_ALPHA_2
        if c not in ISO_3166_ALPHA_2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ISO-3166-1 alpha-2 country code: '{payload.country}'.",
            )
        current_user.country = c
    if payload.timezone is not None:
        import zoneinfo
        tz = payload.timezone.strip()
        if tz not in zoneinfo.available_timezones():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid IANA timezone: '{payload.timezone}'.",
            )
        current_user.timezone = tz
    if payload.languages is not None:
        current_user.languages = [lang.strip().lower() for lang in payload.languages if lang.strip()]
    if payload.subjects_studied is not None:
        current_user.subjects_studied = [validate_slug(s) for s in payload.subjects_studied]
    if payload.preferred_teaching_style is not None:
        current_user.preferences.preferred_teaching_style = payload.preferred_teaching_style
    if payload.learning_goals is not None:
        current_user.preferences.learning_goals = payload.learning_goals
    if payload.audio_only_default is not None:
        current_user.preferences.audio_only_default = payload.audio_only_default

    current_user.updated_at = datetime.now(timezone.utc)
    await current_user.save()

    return APIResponse(success=True, data=_format_user_resp(current_user))


@router.post("/me/verify-student", response_model=APIResponse[dict])
async def request_student_verification(
    payload: VerifyStudentRequest,
    current_user: User = Depends(get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Student institutional verification is disabled until real institutional email verification is implemented.",
    )


class AIConsentRequest(BaseModel):
    ai_consent: bool


@router.post("/me/ai-consent", response_model=APIResponse[dict])
async def update_ai_consent(
    payload: AIConsentRequest,
    current_user: User = Depends(get_current_user),
):
    now_utc = datetime.now(timezone.utc)
    current_user.ai_consent = payload.ai_consent
    current_user.ai_consent_record = {
        "consented": payload.ai_consent,
        "consented_at": now_utc.isoformat(),
        "policy_version": "1.0",
    }
    if not payload.ai_consent:
        current_user.ai_consent_withdrawn_at = now_utc
    else:
        current_user.ai_consent_withdrawn_at = None
    current_user.updated_at = now_utc
    await current_user.save()

    return APIResponse(
        success=True,
        data={
            "ai_consent": current_user.ai_consent,
            "ai_consent_record": current_user.ai_consent_record,
            "ai_consent_withdrawn_at": (
                current_user.ai_consent_withdrawn_at.isoformat()
                if current_user.ai_consent_withdrawn_at
                else None
            ),
            "message": "AI processing consent successfully updated.",
        },
    )


@router.get("/me/export", response_model=APIResponse[DataExportResponse])
async def export_my_data(current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    profile = await SkillProfile.find_one(SkillProfile.user_id == user_id)
    events = await TelemetryEvent.find(TelemetryEvent.user_id == user_id).to_list()
    quiz_attempts = await QuizAttempt.find(QuizAttempt.user_id == user_id).to_list()
    snapshots = await SkillSnapshot.find(SkillSnapshot.user_id == user_id).to_list()
    mistakes = await MistakeEntry.find(MistakeEntry.user_id == user_id).to_list()
    reviews = await ReviewSchedule.find(ReviewSchedule.user_id == user_id).to_list()
    availability = await Availability.find_one(Availability.user_id == user_id)
    pool_entries = await MatchingPoolEntry.find(MatchingPoolEntry.user_id == user_id).to_list()
    push_subs = await PushSubscription.find(PushSubscription.user_id == user_id).to_list()
    messages = await Message.find(Message.sender_id == user_id).to_list()
    peer_quizzes = await PeerQuiz.find(
        {"$or": [{"creator_id": user_id}, {"target_learner_id": user_id}]}
    ).to_list()
    blocks = await Block.find(
        {"$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]}
    ).to_list()
    otp_challenges = await OTPChallenge.find(OTPChallenge.email == current_user.email).to_list()

    user_dict = current_user.model_dump(mode="json")
    user_dict.pop("id", None)

    export_payload = {
        "user_profile": user_dict,
        "skill_matrix": profile.model_dump(mode="json") if profile else {},
        "quiz_attempts": [q.model_dump(mode="json") for q in quiz_attempts],
        "skill_snapshots": [s.model_dump(mode="json") for s in snapshots],
        "mistake_entries": [m.model_dump(mode="json") for m in mistakes],
        "review_schedules": [r.model_dump(mode="json") for r in reviews],
        "availability": availability.model_dump(mode="json") if availability else {},
        "pool_entries": [p.model_dump(mode="json") for p in pool_entries],
        "push_subscriptions": [s.model_dump(mode="json") for s in push_subs],
        "messages": [m.model_dump(mode="json") for m in messages],
        "peer_quizzes": [pq.model_dump(mode="json") for pq in peer_quizzes],
        "blocks": [b.model_dump(mode="json") for b in blocks],
        "otp_challenges": [o.model_dump(mode="json") for o in otp_challenges],
        "telemetry_events": [e.model_dump(mode="json") for e in events],
    }

    return APIResponse(
        success=True,
        data=DataExportResponse(
            user_data=export_payload,
            exported_at=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.delete("/me", response_model=APIResponse[dict])
async def delete_my_account(current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    # Decision Rule: Account deletion is held while a report is under active investigation
    open_report = await Report.find_one(
        {
            "$or": [
                {"reported_user_id": user_id},
                {"reporter_user_id": user_id},
            ],
            "status": {"$in": ["pending", "investigating"]},
        }
    )
    if open_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account deletion is temporarily held while an active Trust & Safety report is pending investigation.",
        )

    # Purge user records across all collections
    await QuizAttempt.find(QuizAttempt.user_id == user_id).delete()
    await SkillSnapshot.find(SkillSnapshot.user_id == user_id).delete()
    await MistakeEntry.find(MistakeEntry.user_id == user_id).delete()
    await ReviewSchedule.find(ReviewSchedule.user_id == user_id).delete()
    await Availability.find(Availability.user_id == user_id).delete()
    await MatchingPoolEntry.find(MatchingPoolEntry.user_id == user_id).delete()
    await PushSubscription.find(PushSubscription.user_id == user_id).delete()
    await Message.find(Message.sender_id == user_id).delete()
    await PeerQuiz.find({"$or": [{"creator_id": user_id}, {"target_learner_id": user_id}]}).delete()
    await Block.find({"$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]}).delete()
    await OTPChallenge.find(OTPChallenge.email == current_user.email).delete()
    await TelemetryEvent.find(TelemetryEvent.user_id == user_id).delete()
    await SkillProfile.find(SkillProfile.user_id == user_id).delete()
    # Delete non-investigating reports
    await Report.find({
        "$or": [{"reported_user_id": user_id}, {"reporter_user_id": user_id}],
        "status": {"$nin": ["pending", "investigating"]},
    }).delete()

    await current_user.delete()
    from app.services.auth_service import AuthService
    await AuthService.revoke_all_user_sessions(str(user_id))

    return APIResponse(
        success=True,
        data={"message": "All user data permanently purged across all collections."},
    )


@router.post("/me/portfolio/regenerate", response_model=APIResponse[dict])
async def regenerate_portfolio_slug(current_user: User = Depends(get_current_user)):
    """Generates a new random unguessable slug server-side."""
    new_slug = secrets.token_urlsafe(12)
    current_user.portfolio_slug = new_slug
    await current_user.save()
    return APIResponse(
        success=True,
        message="Portfolio slug regenerated successfully.",
        data={
            "portfolio_slug": current_user.portfolio_slug,
            "portfolio_is_public": current_user.portfolio_is_public,
        },
    )


@router.post("/me/portfolio/revoke", response_model=APIResponse[dict])
async def revoke_portfolio_slug(current_user: User = Depends(get_current_user)):
    """Revokes the current portfolio slug and makes the portfolio private."""
    current_user.portfolio_slug = None
    current_user.portfolio_is_public = False
    await current_user.save()
    return APIResponse(
        success=True,
        message="Portfolio slug revoked and portfolio set to private.",
        data={
            "portfolio_slug": None,
            "portfolio_is_public": False,
        },
    )


@router.patch("/me/portfolio", response_model=APIResponse[dict])
async def update_my_portfolio(
    data: UpdatePortfolioRequest,
    current_user: User = Depends(get_current_user),
):
    if data.portfolio_is_public:
        if not current_user.portfolio_slug:
            # Generate random unguessable slug server-side
            current_user.portfolio_slug = secrets.token_urlsafe(12)
    current_user.portfolio_is_public = data.portfolio_is_public
    await current_user.save()

    return APIResponse(
        success=True,
        message="Portfolio preferences updated successfully.",
        data={
            "portfolio_slug": current_user.portfolio_slug,
            "portfolio_is_public": current_user.portfolio_is_public,
        },
    )


@router.get("/me/badges", response_model=APIResponse[List[BadgeResponse]])
async def get_my_badges(
    current_user: User = Depends(get_current_user),
):
    await BadgeService.evaluate_user_milestones(current_user.id)
    badges = await BadgeService.get_user_badges(current_user.id)
    return APIResponse(success=True, data=badges)


@router.get("/portfolio/{slug}", response_model=APIResponse[PublicPortfolioResponse])
async def get_public_portfolio(slug: str, response: Response):
    # Set noindex headers for all public portfolio responses
    response.headers["X-Robots-Tag"] = "noindex, nofollow"

    cleaned_slug = validate_slug(slug)
    user = await User.find_one(User.portfolio_slug == cleaned_slug)
    if not user or not user.is_active or not user.portfolio_is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public teaching portfolio not found.",
        )

    # Strictly read-only on public GET: zero write operations
    badges = await BadgeService.get_user_badges(user.id)

    distinct_count = len(user.distinct_partners)
    partner_diversity_unlocked = distinct_count >= 5

    avg_clarity = None
    avg_helpfulness = None
    notice = None

    if not partner_diversity_unlocked:
        notice = f"Verified peer ratings unlock after completing sessions with 5 distinct study partners (current: {distinct_count}/5). This policy prevents reciprocal score inflation."
    else:
        # Calculate verified peer ratings from closed sessions
        closed_sessions = await Session.find({
            "status": "closed",
            "participants.user_id": user.id,
        }).to_list()

        clarities = []
        helpfuls = []
        for s in closed_sessions:
            partner_p = next((p for p in s.participants if p.user_id != user.id), None)
            if partner_p and partner_p.rating_given:
                c = partner_p.rating_given.get("clarity")
                h = partner_p.rating_given.get("helpfulness")
                if c is not None:
                    clarities.append(float(c))
                if h is not None:
                    helpfuls.append(float(h))

        if clarities:
            avg_clarity = round(sum(clarities) / len(clarities), 2)
        if helpfuls:
            avg_helpfulness = round(sum(helpfuls) / len(helpfuls), 2)

    portfolio_data = PublicPortfolioResponse(
        full_name=user.full_name,
        country=user.country,
        timezone=user.timezone,
        portfolio_slug=user.portfolio_slug,
        is_public=user.portfolio_is_public,
        is_verified_student=user.is_verified_student,
        is_mentor=user.is_mentor,
        completed_sessions_count=user.completed_sessions_count,
        distinct_partners_count=distinct_count,
        partner_diversity_unlocked=partner_diversity_unlocked,
        teaching_subjects=user.subjects_studied,
        badges=badges,
        average_clarity_rating=avg_clarity,
        average_helpfulness_rating=avg_helpfulness,
        notice=notice,
    )

    return APIResponse(success=True, data=portfolio_data)
