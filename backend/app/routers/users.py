from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.consolidated import Report, Session, SkillProfile, TelemetryEvent, User, validate_slug
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
        current_user.country = payload.country.upper().strip()
    if payload.timezone is not None:
        current_user.timezone = payload.timezone.strip()
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
    inst_email = payload.institutional_email.lower().strip()
    # Simple sanity check for institutional domain
    if "@" not in inst_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid institutional email address.",
        )

    current_user.institutional_email = inst_email
    current_user.is_verified_student = True  # For MVP simulation; email verification link in production
    await current_user.save()

    return APIResponse(
        success=True,
        data={"message": f"Verification badge enabled for institutional email {inst_email}."},
    )


class AIConsentRequest(BaseModel):
    ai_consent: bool


@router.post("/me/ai-consent", response_model=APIResponse[dict])
async def update_ai_consent(
    payload: AIConsentRequest,
    current_user: User = Depends(get_current_user),
):
    current_user.ai_consent = payload.ai_consent
    if not payload.ai_consent:
        current_user.ai_consent_withdrawn_at = datetime.now(timezone.utc)
    else:
        current_user.ai_consent_withdrawn_at = None
    current_user.updated_at = datetime.now(timezone.utc)
    await current_user.save()

    return APIResponse(
        success=True,
        data={
            "ai_consent": current_user.ai_consent,
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
    profile = await SkillProfile.find_one(SkillProfile.user_id == current_user.id)
    events = await TelemetryEvent.find(TelemetryEvent.user_id == current_user.id).to_list()
    user_dict = current_user.model_dump(mode="json")
    # Redact internal security fields
    user_dict.pop("id", None)
    
    export_payload = {
        "user_profile": user_dict,
        "skill_matrix": profile.model_dump(mode="json") if profile else {},
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

    # Decision Rule: Account deletion is held while a report is open
    open_report = await Report.find_one(
        {
            "$or": [
                {"reported_user_id": user_id},
                {"reporter_user_id": user_id},
            ],
            "status": "pending",
        }
    )
    if open_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account deletion is temporarily held while an active Trust & Safety report is pending investigation.",
        )

    # Purge telemetry events, skill profiles, and user record
    await TelemetryEvent.find(TelemetryEvent.user_id == user_id).delete()
    await SkillProfile.find(SkillProfile.user_id == user_id).delete()
    await current_user.delete()
    from app.services.auth_service import AuthService
    await AuthService.revoke_all_user_sessions(str(user_id))

    return APIResponse(
        success=True,
        data={"message": "Account, profile data, and telemetry events permanently purged."},
    )


@router.patch("/me/portfolio", response_model=APIResponse[dict])
async def update_my_portfolio(
    data: UpdatePortfolioRequest,
    current_user: User = Depends(get_current_user),
):
    if data.portfolio_slug is not None:
        cleaned_slug = validate_slug(data.portfolio_slug)
        existing = await User.find_one(User.portfolio_slug == cleaned_slug)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The portfolio slug '{cleaned_slug}' is already taken. Please choose another.",
            )
        current_user.portfolio_slug = cleaned_slug

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
async def get_public_portfolio(slug: str):
    cleaned_slug = validate_slug(slug)
    user = await User.find_one(User.portfolio_slug == cleaned_slug)
    if not user or not user.is_active or not user.portfolio_is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public teaching portfolio not found.",
        )

    # Evaluate milestones
    await BadgeService.evaluate_user_milestones(user.id)
    badges = await BadgeService.get_user_badges(user.id)

    distinct_count = len(user.distinct_partners)
    partner_diversity_unlocked = distinct_count >= 5

    avg_clarity = None
    avg_helpfulness = None
    notice = None

    if not partner_diversity_unlocked:
        notice = f"Verified peer ratings unlock after completing sessions with 5 distinct study partners (current: {distinct_count}/5). This policy prevents reciprocal score inflation."
    else:
        # Calculate true verified peer ratings
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
