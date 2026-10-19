from typing import Dict, List
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.consolidated import SkillProfile, SkillSnapshot, User
from app.schemas.common import APIResponse
from app.schemas.skills import (
    SkillProfileResponse,
    SkillSnapshotDetail,
    TopicSkillDetail,
)

router = APIRouter(prefix="/skills", tags=["Skills & Mastery"])


@router.get("/me", response_model=APIResponse[SkillProfileResponse])
async def get_my_skills(
    current_user: User = Depends(get_current_user),
):
    profile = await SkillProfile.find_one(SkillProfile.user_id == current_user.id)
    snapshots = await SkillSnapshot.find(
        SkillSnapshot.user_id == current_user.id,
    ).sort("-recorded_at").limit(30).to_list()

    subjects_dict: Dict[str, Dict[str, TopicSkillDetail]] = {}
    last_diag_dict: Dict[str, str] = {}

    if profile:
        for subj, topics in profile.subjects.items():
            subjects_dict[subj] = {}
            for t_slug, t_skill in topics.items():
                subjects_dict[subj][t_slug] = TopicSkillDetail(
                    score=t_skill.score,
                    confidence_level=t_skill.confidence_level,
                    last_assessed_at=t_skill.last_assessed_at.isoformat() if t_skill.last_assessed_at else None,
                    diagnostic_attempts_count=t_skill.diagnostic_attempts_count,
                )

        for subj, dt in profile.last_diagnostic_at.items():
            last_diag_dict[subj] = dt.isoformat()

    snapshot_details: List[SkillSnapshotDetail] = [
        SkillSnapshotDetail(
            subject_slug=snap.subject_slug,
            topic_slug=snap.topic_slug,
            score=snap.score,
            source_type=snap.source_type,
            source_id=str(snap.source_id),
            recorded_at=snap.recorded_at.isoformat(),
        )
        for snap in snapshots
    ]

    return APIResponse(
        success=True,
        data=SkillProfileResponse(
            user_id=str(current_user.id),
            subjects=subjects_dict,
            last_diagnostic_at=last_diag_dict,
            recent_snapshots=snapshot_details,
        ),
    )
