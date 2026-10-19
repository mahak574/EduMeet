import logging
from datetime import datetime, timezone
from typing import List, Optional
from beanie import PydanticObjectId

from app.models.consolidated import Badge, PeerQuiz, Session, User
from app.schemas.portfolio import BadgeResponse

logger = logging.getLogger(__name__)

DEFINED_BADGES = {
    "first_session": {
        "title": "First Reciprocal Step",
        "description": "Completed your first reciprocal peer teaching session.",
        "icon_name": "Sparkles",
    },
    "five_partners": {
        "title": "Network Builder",
        "description": "Collaborated with 5 distinct study partners, unlocking verified public ratings.",
        "icon_name": "Users",
    },
    "clarity_champion": {
        "title": "Clarity Champion",
        "description": "Maintained an exceptional average peer clarity rating of 4.5+ across 5+ sessions.",
        "icon_name": "Star",
    },
    "peer_examiner": {
        "title": "Peer Examiner",
        "description": "Authored insightful peer quiz questions during reciprocal teaching exchanges.",
        "icon_name": "HelpCircle",
    },
    "mentor_scholar": {
        "title": "Mentor Scholar",
        "description": "Verified peer mentor status recognized by the academic community.",
        "icon_name": "ShieldCheck",
    },
}


class BadgeService:
    @classmethod
    async def award_badge(cls, user_id: PydanticObjectId, badge_key: str) -> Optional[Badge]:
        if badge_key not in DEFINED_BADGES:
            return None

        existing = await Badge.find_one(
            Badge.user_id == user_id,
            Badge.badge_key == badge_key,
        )
        if existing:
            return existing

        meta = DEFINED_BADGES[badge_key]
        badge = Badge(
            user_id=user_id,
            badge_key=badge_key,
            title=meta["title"],
            description=meta["description"],
            icon_name=meta["icon_name"],
            awarded_at=datetime.now(timezone.utc),
        )
        await badge.insert()
        logger.info("Awarded badge '%s' to user %s", badge_key, user_id)
        return badge

    @classmethod
    async def evaluate_user_milestones(cls, user_id: PydanticObjectId) -> List[Badge]:
        user = await User.get(user_id)
        if not user:
            return []

        awarded: List[Badge] = []

        # 1. First session
        if user.completed_sessions_count >= 1:
            b = await cls.award_badge(user_id, "first_session")
            if b:
                awarded.append(b)

        # 2. Five distinct partners
        if len(user.distinct_partners) >= 5:
            b = await cls.award_badge(user_id, "five_partners")
            if b:
                awarded.append(b)

        # 3. Peer author check
        authored_quizzes = await PeerQuiz.find(PeerQuiz.creator_id == user_id).count()
        if authored_quizzes >= 2:
            b = await cls.award_badge(user_id, "peer_examiner")
            if b:
                awarded.append(b)

        # 4. Mentor check
        if user.is_mentor:
            b = await cls.award_badge(user_id, "mentor_scholar")
            if b:
                awarded.append(b)

        # 5. Clarity Champion check
        if user.completed_sessions_count >= 5:
            closed_sessions = await Session.find({
                "status": "closed",
                "participants.user_id": user_id,
            }).to_list()

            ratings = []
            for s in closed_sessions:
                partner_p = next((p for p in s.participants if p.user_id != user_id), None)
                if partner_p and partner_p.rating_given:
                    ratings.append(partner_p.rating_given.get("clarity", 5.0))

            if ratings and (sum(ratings) / len(ratings)) >= 4.5:
                b = await cls.award_badge(user_id, "clarity_champion")
                if b:
                    awarded.append(b)

        return awarded

    @classmethod
    async def get_user_badges(cls, user_id: PydanticObjectId) -> List[BadgeResponse]:
        badges = await Badge.find(Badge.user_id == user_id).sort("-awarded_at").to_list()
        return [
            BadgeResponse(
                badge_key=b.badge_key,
                title=b.title,
                description=b.description,
                icon_name=b.icon_name,
                awarded_at=b.awarded_at,
            )
            for b in badges
        ]
