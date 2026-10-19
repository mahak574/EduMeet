import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.consolidated import (
    Question,
    QuizAttempt,
    Session,
    SkillProfile,
    SkillSnapshot,
    TopicSkill,
    User,
)
from app.services.review_service import ReviewService

logger = logging.getLogger(__name__)


class EvaluationService:
    @classmethod
    async def get_postcheck_questions(
        cls, session_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> List[Dict[str, Any]]:
        """
        Returns 3 held-out diagnostic items on the topic learned in this session.
        Excludes questions served in prior diagnostics AND the pre-check.
        """
        session = await Session.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        user_p = next((p for p in session.participants if p.user_id == user_id), None)
        if not user_p:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

        # Find questions served in diagnostics
        past_attempts = await QuizAttempt.find(QuizAttempt.user_id == user_id).to_list()
        excluded_ids = set()
        for att in past_attempts:
            excluded_ids.update(att.served_question_ids)

        all_qs = await Question.find({
            "subject_slug": user_p.learn_subject_slug,
            "topic_slug": user_p.learn_topic_slug,
            "review_status": "approved",
        }).to_list()

        unserved = [q for q in all_qs if q.id not in excluded_ids]
        selected_qs = unserved[:3] if len(unserved) >= 3 else all_qs[:3]

        return [
            {
                "question_id": str(q.id),
                "subject_slug": q.subject_slug,
                "topic_slug": q.topic_slug,
                "difficulty": q.difficulty,
                "prompt_text": q.prompt_text,
                "code_snippet": q.code_snippet,
                "options": [{"id": opt.id, "text": opt.text} for opt in q.options],
            }
            for q in selected_qs
        ]

    @classmethod
    async def submit_postcheck(
        cls,
        session_id: PydanticObjectId,
        user_id: PydanticObjectId,
        answers: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Grades post-check, creates post-session SkillSnapshot, updates SkillProfile, and logs mistakes.
        """
        session = await Session.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        user_p = next((p for p in session.participants if p.user_id == user_id), None)
        if not user_p:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

        total = len(answers)
        correct_count = 0

        for q_id_str, selected_opt in answers.items():
            try:
                q = await Question.get(PydanticObjectId(q_id_str))
                if q:
                    if q.correct_option_id == selected_opt:
                        correct_count += 1
                    else:
                        # Log mistake to SM-2 queue
                        await ReviewService.log_mistake(
                            user_id=user_id,
                            subject_slug=q.subject_slug,
                            topic_slug=q.topic_slug,
                            subtopic_slug=q.subtopic_slug,
                            question_ref_id=q.id,
                            question_prompt=q.prompt_text,
                            mistake_tag="didnt_know_concept",
                            learner_notes=f"Post-check mistake: selected {selected_opt}, correct was {q.correct_option_id}",
                        )
            except Exception:
                continue

        post_score_pct = round((correct_count / max(1, total)) * 100.0, 1)

        # Retrieve pre-session score if available
        pre_score_pct = None
        if user_p.pre_session_snapshot_id:
            pre_snap = await SkillSnapshot.get(user_p.pre_session_snapshot_id)
            if pre_snap:
                pre_score_pct = pre_snap.score

        delta = round(post_score_pct - (pre_score_pct or 50.0), 1)

        # Create Post-Session SkillSnapshot
        post_snapshot = SkillSnapshot(
            user_id=user_id,
            subject_slug=user_p.learn_subject_slug,
            topic_slug=user_p.learn_topic_slug,
            score=post_score_pct,
            source_type="post_session",
            source_id=session.id,
        )
        await post_snapshot.insert()
        user_p.post_session_snapshot_id = post_snapshot.id
        await session.save()

        # Update SkillProfile with post-session observation
        profile = await SkillProfile.find_one(SkillProfile.user_id == user_id)
        if profile:
            subj = user_p.learn_subject_slug
            topic = user_p.learn_topic_slug
            if subj in profile.subjects and topic in profile.subjects[subj]:
                old_score = profile.subjects[subj][topic].score
                # Session post-check observation weight: 30% session, 70% historical baseline
                updated_score = round(old_score * 0.70 + post_score_pct * 0.30, 1)
                profile.subjects[subj][topic].overall_score = updated_score
                profile.subjects[subj][topic].last_assessed_at = datetime.now(timezone.utc)
                await profile.save()

        logger.info("User %s completed post-check for session %s: %.1f%% (delta: %+.1f%%)", user_id, session_id, post_score_pct, delta)
        return {
            "session_id": str(session.id),
            "pre_score_percentage": pre_score_pct,
            "post_score_percentage": post_score_pct,
            "learning_gain_delta": delta,
            "total_questions": total,
            "correct_count": correct_count,
            "snapshot_id": str(post_snapshot.id),
        }

    @classmethod
    async def submit_session_rating(
        cls,
        session_id: PydanticObjectId,
        user_id: PydanticObjectId,
        clarity: float,
        helpfulness: float,
        feedback_text: Optional[str] = None,
    ) -> Session:
        """
        Records 5-star ratings and updates partner's completed session count and partner diversity.
        """
        session = await Session.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        user_p = next((p for p in session.participants if p.user_id == user_id), None)
        partner_p = next((p for p in session.participants if p.user_id != user_id), None)

        if not user_p or not partner_p:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

        # Save rating
        user_p.rating_given = {
            "clarity": round(clarity, 1),
            "helpfulness": round(helpfulness, 1),
        }
        user_p.feedback_text = feedback_text
        await session.save()

        # Update partner's reliability & partner diversity stats
        partner_user = await User.get(partner_p.user_id)
        if partner_user:
            partner_user.completed_sessions_count += 1
            if user_id not in partner_user.distinct_partners:
                partner_user.distinct_partners.append(user_id)
            if len(partner_user.distinct_partners) >= 5:
                partner_user.portfolio_is_public = True
            await partner_user.save()

        logger.info("User %s rated partner %s in session %s: clarity=%.1f, helpfulness=%.1f", user_id, partner_p.user_id, session_id, clarity, helpfulness)
        return session
