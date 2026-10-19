from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.consolidated import Report, SkillProfile, TelemetryEvent, User, validate_slug
from app.schemas.auth import UserResponse
from app.schemas.common import APIResponse
from app.schemas.profile import DataExportResponse, UpdateProfileRequest, VerifyStudentRequest

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
