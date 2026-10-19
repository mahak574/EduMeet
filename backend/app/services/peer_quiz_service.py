import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.consolidated import PeerQuestion, PeerQuiz, Session
from app.services.review_service import ReviewService

logger = logging.getLogger(__name__)


class PeerQuizService:
    @classmethod
    async def create_or_update_peer_quiz(
        cls,
        session_id: PydanticObjectId,
        creator_id: PydanticObjectId,
        questions: List[Dict[str, Any]],
    ) -> PeerQuiz:
        """
        Creates or updates a peer quiz drafted by the teacher for their learning partner.
        """
        session = await Session.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        creator_p = next((p for p in session.participants if p.user_id == creator_id), None)
        learner_p = next((p for p in session.participants if p.user_id != creator_id), None)

        if not creator_p or not learner_p:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

        # Format questions
        peer_questions = [
            PeerQuestion(
                question_type=q.get("question_type", "mcq"),
                prompt=q["prompt"],
                options=q.get("options", []),
                correct_option_index=q.get("correct_option_index", 0),
            )
            for q in questions
        ]

        quiz = await PeerQuiz.find_one(
            PeerQuiz.session_id == session_id,
            PeerQuiz.creator_id == creator_id,
        )

        now = datetime.now(timezone.utc)
        if not quiz:
            quiz = PeerQuiz(
                session_id=session_id,
                creator_id=creator_id,
                target_learner_id=learner_p.user_id,
                subject_slug=creator_p.teach_subject_slug,
                topic_slug=creator_p.teach_topic_slug,
                questions=peer_questions,
                submitted_at=now,
            )
            await quiz.insert()
        else:
            quiz.questions = peer_questions
            quiz.submitted_at = now
            await quiz.save()

        logger.info("Peer quiz created by user %s for partner %s in session %s", creator_id, learner_p.user_id, session_id)
        return quiz

    @classmethod
    async def get_quiz_for_learner(
        cls, session_id: PydanticObjectId, learner_id: PydanticObjectId
    ) -> Optional[PeerQuiz]:
        """Returns the peer quiz prepared for this learner."""
        return await PeerQuiz.find_one(
            PeerQuiz.session_id == session_id,
            PeerQuiz.target_learner_id == learner_id,
        )

    @classmethod
    async def get_quiz_created_by(
        cls, session_id: PydanticObjectId, creator_id: PydanticObjectId
    ) -> Optional[PeerQuiz]:
        """Returns the peer quiz drafted by this creator."""
        return await PeerQuiz.find_one(
            PeerQuiz.session_id == session_id,
            PeerQuiz.creator_id == creator_id,
        )

    @classmethod
    async def submit_answers(
        cls,
        session_id: PydanticObjectId,
        learner_id: PydanticObjectId,
        answers: List[Dict[str, Any]],
    ) -> PeerQuiz:
        """
        Grades learner answers, logs mistakes for incorrect responses, and records clarity feedback.
        """
        quiz = await cls.get_quiz_for_learner(session_id, learner_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No peer quiz found for you in this session.")

        total = len(quiz.questions)
        correct_count = 0

        # Map answers by question index
        ans_map = {a["question_index"]: a for a in answers}

        for idx, q in enumerate(quiz.questions):
            ans = ans_map.get(idx)
            if not ans:
                continue

            q.partner_answer = str(ans.get("partner_answer", ""))
            q.partner_clarity_rating = ans.get("clarity_rating", "clear")

            # Grade MCQ
            if q.question_type == "mcq" and q.correct_option_index is not None:
                try:
                    selected_idx = int(q.partner_answer)
                    is_correct = selected_idx == q.correct_option_index
                except Exception:
                    is_correct = False

                q.is_auto_graded_correct = is_correct
                if is_correct:
                    correct_count += 1
                else:
                    # Log mistake into spaced repetition review queue
                    await ReviewService.log_mistake(
                        user_id=learner_id,
                        subject_slug=quiz.subject_slug,
                        topic_slug=quiz.topic_slug,
                        subtopic_slug="peer_quiz",
                        question_ref_id=quiz.id,
                        question_prompt=q.prompt,
                        mistake_tag="didnt_know_concept",
                        learner_notes=f"Peer quiz error: selected {q.partner_answer}, correct was {q.correct_option_index}",
                    )

        quiz.graded_at = datetime.now(timezone.utc)
        await quiz.save()

        logger.info("Learner %s completed peer quiz in session %s (%d/%d correct)", learner_id, session_id, correct_count, total)
        return quiz
