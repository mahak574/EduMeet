from typing import Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.consolidated import Match, User
from app.schemas.matching import (
    MatchConfirmRequest,
    MatchDeclineRequest,
    MatchingCycleRunResponse,
    MatchPartyInfo,
    MatchResponse,
    PoolJoinRequest,
    PoolStatusResponse,
)
from app.schemas.common import APIResponse
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/pool/join", response_model=APIResponse[PoolStatusResponse])
async def join_matching_pool(
    req: PoolJoinRequest,
    current_user: User = Depends(get_current_user),
):
    entry = await MatchingService.join_pool(current_user.id, req.subject_slugs)
    return APIResponse(
        success=True,
        data=PoolStatusResponse(
            is_in_pool=entry.status == "active",
            subject_slugs=entry.subject_slugs,
            entered_at=entry.entered_at,
            status=entry.status,
        ),
    )


@router.post("/pool/leave", response_model=APIResponse[dict])
async def leave_matching_pool(
    current_user: User = Depends(get_current_user),
):
    success = await MatchingService.leave_pool(current_user.id)
    return APIResponse(success=True, data={"left": success})


@router.get("/pool/status", response_model=APIResponse[PoolStatusResponse])
async def get_matching_pool_status(
    current_user: User = Depends(get_current_user),
):
    entry = await MatchingService.get_pool_status(current_user.id)
    if not entry or entry.status != "active":
        return APIResponse(
            success=True,
            data=PoolStatusResponse(is_in_pool=False, subject_slugs=[], status=entry.status if entry else None),
        )

    return APIResponse(
        success=True,
        data=PoolStatusResponse(
            is_in_pool=True,
            subject_slugs=entry.subject_slugs,
            entered_at=entry.entered_at,
            status=entry.status,
        ),
    )


@router.get("/status", response_model=APIResponse[Optional[MatchResponse]])
async def get_matching_status(
    current_user: User = Depends(get_current_user),
):
    match = await MatchingService.get_active_match(current_user.id)
    if not match:
        return APIResponse(success=True, data=None)

    # Format response with personalized perspective
    user_party = next((p for p in match.participants if p.user_id == current_user.id), None)
    partner_party = next((p for p in match.participants if p.user_id != current_user.id), None)

    partner_name = "Peer Student"
    partner_id = None
    if partner_party:
        partner_id = str(partner_party.user_id)
        partner_user = await User.get(partner_party.user_id)
        if partner_user:
            partner_name = partner_user.full_name

    parties_info = []
    for p in match.participants:
        u = await User.get(p.user_id)
        parties_info.append(
            MatchPartyInfo(
                user_id=str(p.user_id),
                user_name=u.full_name if u else "Student",
                teach_subject_slug=p.teach_subject_slug,
                teach_topic_slug=p.teach_topic_slug,
                learn_subject_slug=p.learn_subject_slug,
                learn_topic_slug=p.learn_topic_slug,
                confirmed=p.confirmed,
                confirmed_at=p.confirmed_at,
                selected_slot=p.selected_slot,
            )
        )

    resp = MatchResponse(
        id=str(match.id),
        status=match.status,
        score=match.score,
        common_languages=match.common_languages,
        proposed_slots=match.proposed_slots,
        expires_at=match.expires_at,
        session_id=str(match.session_id) if match.session_id else None,
        my_teach_subject=user_party.teach_subject_slug if user_party else None,
        my_teach_topic=user_party.teach_topic_slug if user_party else None,
        my_learn_subject=user_party.learn_subject_slug if user_party else None,
        my_learn_topic=user_party.learn_topic_slug if user_party else None,
        partner_name=partner_name,
        partner_id=partner_id,
        has_confirmed=user_party.confirmed if user_party else False,
        partner_has_confirmed=partner_party.confirmed if partner_party else False,
        participants=parties_info,
    )
    return APIResponse(success=True, data=resp)


@router.post("/confirm", response_model=APIResponse[dict])
async def confirm_match(
    req: MatchConfirmRequest,
    match_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    match, session = await MatchingService.confirm_match(
        user_id=current_user.id,
        match_id=match_id,
        chosen_slot=req.chosen_slot,
    )
    return APIResponse(
        success=True,
        data={
            "match_id": str(match.id),
            "match_status": match.status,
            "session_id": str(session.id) if session else None,
            "is_mutual": session is not None,
        },
    )


@router.post("/decline", response_model=APIResponse[dict])
async def decline_match(
    req: MatchDeclineRequest,
    match_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    success = await MatchingService.decline_match(
        user_id=current_user.id,
        match_id=match_id,
        reason=req.reason,
    )
    return APIResponse(success=True, data={"declined": success})


@router.post("/run", response_model=APIResponse[MatchingCycleRunResponse])
async def trigger_matching_cycle(
    current_user: User = Depends(get_current_user),
):
    """Admin or automated trigger to execute the matching cycle immediately."""
    matches = await MatchingService.run_matching_cycle()
    return APIResponse(
        success=True,
        data=MatchingCycleRunResponse(
            matches_created_count=len(matches),
            pool_candidates_count=0,
            match_ids=[str(m.id) for m in matches],
        ),
    )
