import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.consolidated import MistakeEntry, ReviewSchedule

logger = logging.getLogger(__name__)


def apply_sm2(
    repetition: int,
    easiness_factor: float,
    interval_days: int,
    quality: int,
) -> Tuple[int, float, int]:
    """
    Standard SuperMemo-2 (SM-2) spaced repetition algorithm:
    q in [0, 5]:
      5: perfect response
      4: correct response after hesitation
      3: correct response recalled with serious difficulty
      2: incorrect response; where the correct one seemed easy to recall
      1: incorrect response; the correct one remembered
      0: complete blackout
    """
    new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, round(new_ef, 3))

    if quality < 3:
        # Reset on lapse
        new_rep = 0
        new_interval = 1
    else:
        if repetition == 0:
            new_interval = 1
        elif repetition == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(interval_days * new_ef))
        new_rep = repetition + 1

    return new_rep, new_ef, new_interval


class ReviewService:
    @classmethod
    async def log_mistake(
        cls,
        user_id: PydanticObjectId,
        subject_slug: str,
        topic_slug: str,
        subtopic_slug: str,
        question_ref_id: PydanticObjectId,
        question_prompt: str,
        mistake_tag: str = "didnt_know_concept",
        learner_notes: Optional[str] = None,
    ) -> MistakeEntry:
        """
        Logs an incorrect answer into the Mistake Journal and initializes/schedules SM-2 review.
        """
        entry = MistakeEntry(
            user_id=user_id,
            subject_slug=subject_slug,
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug or "general",
            question_ref_id=question_ref_id,
            question_prompt=question_prompt,
            user_mistake_tag=mistake_tag,
            learner_notes=learner_notes,
            created_at=datetime.now(timezone.utc),
        )
        await entry.insert()

        # Initialize or update ReviewSchedule for this user and subtopic
        now = datetime.now(timezone.utc)
        schedule = await ReviewSchedule.find_one(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.subject_slug == subject_slug,
            ReviewSchedule.subtopic_slug == subtopic_slug,
        )

        if not schedule:
            schedule = ReviewSchedule(
                user_id=user_id,
                subject_slug=subject_slug,
                subtopic_slug=subtopic_slug,
                repetition_number=0,
                easiness_factor=2.5,
                interval_days=1,
                next_review_date=now + timedelta(days=1),
            )
            await schedule.insert()
        else:
            # If a mistake happened, bring forward review date to tomorrow
            schedule.next_review_date = min(schedule.next_review_date, now + timedelta(days=1))
            await schedule.save()

        logger.info("Logged mistake for user %s on %s/%s", user_id, subject_slug, topic_slug)
        return entry

    @classmethod
    async def get_due_reviews(cls, user_id: PydanticObjectId) -> List[ReviewSchedule]:
        """Returns all review schedules due for the user."""
        now = datetime.now(timezone.utc)
        return await ReviewSchedule.find(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.next_review_date <= now,
        ).to_list()

    @classmethod
    async def get_all_schedules(cls, user_id: PydanticObjectId) -> List[ReviewSchedule]:
        """Returns all spaced repetition schedules for user."""
        return await ReviewSchedule.find(ReviewSchedule.user_id == user_id).to_list()

    @classmethod
    async def evaluate_review(
        cls,
        user_id: PydanticObjectId,
        schedule_id: PydanticObjectId,
        quality_rating: int,
    ) -> ReviewSchedule:
        """
        Updates review schedule using the SuperMemo-2 algorithm based on recall quality (0-5).
        """
        schedule = await ReviewSchedule.get(schedule_id)
        if not schedule or schedule.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review schedule not found.")

        new_rep, new_ef, new_interval = apply_sm2(
            repetition=schedule.repetition_number,
            easiness_factor=schedule.easiness_factor,
            interval_days=schedule.interval_days,
            quality=quality_rating,
        )

        now = datetime.now(timezone.utc)
        schedule.repetition_number = new_rep
        schedule.easiness_factor = new_ef
        schedule.interval_days = new_interval
        schedule.last_reviewed_at = now
        schedule.next_review_date = now + timedelta(days=new_interval)
        await schedule.save()

        logger.info(
            "User %s evaluated review %s: q=%d -> next in %d days (rep=%d, ef=%.2f)",
            user_id, schedule_id, quality_rating, new_interval, new_rep, new_ef,
        )
        return schedule

    @classmethod
    async def get_mistakes(
        cls,
        user_id: PydanticObjectId,
        subject_slug: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[MistakeEntry]:
        """Queries user mistake entries with optional filters."""
        query = {"user_id": user_id}
        if subject_slug:
            query["subject_slug"] = subject_slug
        if resolved is not None:
            query["resolved"] = resolved

        return await MistakeEntry.find(query).sort("-created_at").to_list()

    @classmethod
    async def resolve_mistake(
        cls, user_id: PydanticObjectId, mistake_id: PydanticObjectId
    ) -> MistakeEntry:
        """Marks a mistake entry as understood / resolved."""
        mistake = await MistakeEntry.get(mistake_id)
        if not mistake or mistake.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mistake entry not found.")

        mistake.resolved = True
        await mistake.save()
        return mistake
