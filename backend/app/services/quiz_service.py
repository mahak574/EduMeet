import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.consolidated import (
    Question,
    QuestionItemAttempt,
    QuizAttempt,
    SkillProfile,
    SkillSnapshot,
    TopicSkill,
    User,
    validate_slug,
)
from app.services.ai_question_generator import AIQuestionGenerator, KNOWN_SUBJECT_TOPICS

logger = logging.getLogger(__name__)

# Difficulty weights according to Phase 0.2 patched decisions
DIFFICULTY_WEIGHTS = {
    "easy": 1.0,
    "medium": 1.5,
    "hard": 2.0,
}

# Bayesian shrinkage parameter (simulation-tuned provisional default)
DEFAULT_SHRINKAGE_M = 4.0
DEFAULT_PRIOR_MU = 0.5

# Time limit per question (in seconds)
QUESTION_TIME_LIMIT_SECONDS = 60
NETWORK_BUFFER_SECONDS = 5

# Topics per Phase 2 subject
SUBJECT_TOPICS: Dict[str, List[str]] = {
    "dsa": [
        "arrays-and-hashing",
        "linked-lists-and-stacks",
        "trees-and-graphs",
        "dynamic-programming",
    ],
    "dbms": [
        "relational-schema-and-sql",
        "indexing-and-query-opt",
        "transactions-and-acid",
        "concurrency-and-recovery",
    ],
}


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class QuizService:
    @staticmethod
    async def get_all_served_question_ids(user_id: PydanticObjectId, subject_slug: str) -> set[PydanticObjectId]:
        """
        Retrieves all question IDs previously served to the user in diagnostics or pre/post checks.
        """
        attempts = await QuizAttempt.find(
            QuizAttempt.user_id == user_id,
            QuizAttempt.subject_slug == subject_slug,
        ).to_list()

        served: set[PydanticObjectId] = set()
        for att in attempts:
            served.update(att.served_question_ids)
            # Also catch any assigned questions in legacy attempts
            served.update(att.assigned_question_ids)
        return served

    @staticmethod
    def get_topic_classification(score: float) -> str:
        """
        Classifies topic mastery:
        >= 70.0% -> 'proficient' (strong topic, verified ready to teach)
        < 70.0%  -> 'learning_target' (weak topic, target for practice/peer tutoring)
        """
        return "proficient" if score >= 70.0 else "learning_target"

    @staticmethod
    async def can_start_diagnostic(user_id: PydanticObjectId, subject_slug: str) -> Tuple[bool, Optional[str]]:
        """
        Validates the 3-attempt quota and the 7-day cooldown (measured from completed_at
        or expires_at for abandoned attempts) for any dynamic subject.
        """
        try:
            cleaned_subject = validate_slug(subject_slug)
        except ValueError as val_err:
            return False, str(val_err)

        # Fetch past attempts sorted descending
        attempts = await QuizAttempt.find(
            QuizAttempt.user_id == user_id,
            QuizAttempt.subject_slug == cleaned_subject,
        ).sort("-started_at").to_list()

        # Check 3-attempt limit
        if len(attempts) >= 3:
            return False, "You have reached the maximum limit of 3 diagnostic attempts for this subject."

        now = datetime.now(timezone.utc)

        if attempts:
            latest = attempts[0]
            latest_expires = _ensure_utc(latest.expires_at)
            # If an attempt is currently in progress and not expired, user should resume it
            if not latest.is_completed and latest_expires and now < latest_expires:
                return False, f"You have an active in-progress attempt for {cleaned_subject}. Please resume it."

            # Calculate 7-day cooldown reference point
            cooldown_reference = _ensure_utc(latest.completed_at if latest.is_completed else latest.expires_at)
            if cooldown_reference:
                cooldown_expiry = cooldown_reference + timedelta(days=7)
                if now < cooldown_expiry:
                    remaining_hours = int((cooldown_expiry - now).total_seconds() // 3600)
                    return False, f"Cooldown active. You can retake this diagnostic in {remaining_hours} hours."

        return True, None

    @staticmethod
    async def start_diagnostic(user_id: PydanticObjectId, subject_slug: str) -> QuizAttempt:
        """
        Samples 15-20 questions (3-4 per topic across difficulty tiers), excludes previously
        served questions, handles post-exhaustion repeats, and initializes the QuizAttempt.
        Dynamically supports any subject and topic entered by the user.
        """
        cleaned_subject = validate_slug(subject_slug)
        can_start, reason = await QuizService.can_start_diagnostic(user_id, cleaned_subject)
        if not can_start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

        # Ensure topics and dynamic questions exist for this subject
        topics = await AIQuestionGenerator.ensure_questions_for_subject(cleaned_subject, target_per_topic=4)
        previously_served = await QuizService.get_all_served_question_ids(user_id, cleaned_subject)

        selected_questions: List[Tuple[Question, bool]] = []  # (Question, repeat_exposure)

        for topic in topics:
            # Query approved questions for this topic
            all_topic_questions = await Question.find(
                Question.subject_slug == cleaned_subject,
                Question.topic_slug == topic,
                Question.review_status == "approved",
            ).to_list()

            if not all_topic_questions:
                continue

            # Unserved vs already served
            unserved = [q for q in all_topic_questions if q.id not in previously_served]

            # We aim for 3-4 questions per topic (target 4 questions per topic = 16 questions total)
            target_per_topic = min(4, len(all_topic_questions))

            if len(unserved) >= target_per_topic:
                # Ample fresh questions: sample across difficulty tiers
                sample = random.sample(unserved, target_per_topic)
                for q in sample:
                    selected_questions.append((q, False))
            else:
                # Post-exhaustion policy: take all available unserved, fill remaining with oldest served
                for q in unserved:
                    selected_questions.append((q, False))

                needed = target_per_topic - len(unserved)
                served_topic_questions = [q for q in all_topic_questions if q.id in previously_served]
                # Sort by created_at (oldest first)
                served_topic_questions.sort(key=lambda x: x.created_at)
                repeat_sample = served_topic_questions[:needed]
                for q in repeat_sample:
                    selected_questions.append((q, True))  # Flag repeat_exposure = True

        if not selected_questions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Insufficient approved questions available for subject '{subject_slug}'.",
            )

        # Shuffle selected questions to randomize topic presentation
        random.shuffle(selected_questions)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=2)

        assigned_ids = [q[0].id for q in selected_questions]
        items: List[QuestionItemAttempt] = []

        # Create item attempts; mark repeat questions if applicable
        for q, is_repeat in selected_questions:
            item = QuestionItemAttempt(
                question_id=q[0].id if isinstance(q, tuple) else q.id,
                time_limit_seconds=QUESTION_TIME_LIMIT_SECONDS,
            )
            items.append(item)

        # Count prior attempts to determine attempt_number
        prior_count = await QuizAttempt.find(
            QuizAttempt.user_id == user_id,
            QuizAttempt.subject_slug == subject_slug,
        ).count()

        attempt = QuizAttempt(
            user_id=user_id,
            subject_slug=subject_slug,
            attempt_number=prior_count + 1,
            started_at=now,
            expires_at=expires_at,
            assigned_question_ids=assigned_ids,
            served_question_ids=assigned_ids,
            current_question_index=0,
            items=items,
            resume_count=0,
            max_resumes=2,
            tab_switch_count=0,
            is_completed=False,
        )
        await attempt.insert()
        return attempt

    @staticmethod
    async def get_current_question(attempt_id: PydanticObjectId, user_id: PydanticObjectId) -> Dict[str, any]:
        """
        Retrieves the currently active question for the diagnostic without leaking correct answer.
        """
        attempt = await QuizAttempt.get(attempt_id)
        if not attempt or attempt.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        now = datetime.now(timezone.utc)
        if attempt.is_completed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz attempt is already completed.")

        expires_utc = _ensure_utc(attempt.expires_at)
        if expires_utc and now > expires_utc:
            attempt.is_completed = True
            await attempt.save()
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Quiz attempt has expired.")

        if attempt.current_question_index >= len(attempt.assigned_question_ids):
            attempt.is_completed = True
            await QuizService._finalize_attempt(attempt)
            return {"is_completed": True}

        curr_q_id = attempt.assigned_question_ids[attempt.current_question_index]
        question = await Question.get(curr_q_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

        # Update served timestamp on current item attempt if not already set
        if attempt.current_question_index < len(attempt.items):
            item = attempt.items[attempt.current_question_index]
            item.served_at = datetime.now(timezone.utc)
            await attempt.save()

        return {
            "attempt_id": str(attempt.id),
            "subject_slug": attempt.subject_slug,
            "current_index": attempt.current_question_index,
            "total_questions": len(attempt.assigned_question_ids),
            "question_id": str(question.id),
            "topic_slug": question.topic_slug,
            "difficulty": question.difficulty,
            "prompt_text": question.prompt_text,
            "code_snippet": question.code_snippet,
            "options": [{"id": opt.id, "text": opt.text} for opt in question.options],
            "time_limit_seconds": QUESTION_TIME_LIMIT_SECONDS,
            "expires_at": attempt.expires_at.isoformat(),
            "tab_switch_count": attempt.tab_switch_count,
        }

    @staticmethod
    async def submit_answer(
        attempt_id: PydanticObjectId,
        user_id: PydanticObjectId,
        selected_option_id: Optional[str],
        elapsed_seconds: float,
    ) -> Dict[str, any]:
        """
        Submits answer for the current question, enforces the 60s timer (with 5s buffer),
        scores correctness, and advances to the next question.
        """
        attempt = await QuizAttempt.get(attempt_id)
        if not attempt or attempt.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        if attempt.is_completed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz attempt is already completed.")

        now = datetime.now(timezone.utc)
        expires_utc = _ensure_utc(attempt.expires_at)
        if expires_utc and now > expires_utc:
            attempt.is_completed = True
            await attempt.save()
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Quiz attempt has expired.")

        idx = attempt.current_question_index
        if idx >= len(attempt.assigned_question_ids):
            attempt.is_completed = True
            await QuizService._finalize_attempt(attempt)
            return {"is_completed": True}

        curr_q_id = attempt.assigned_question_ids[idx]
        question = await Question.get(curr_q_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

        # Determine if timed out
        is_timed_out = elapsed_seconds > (QUESTION_TIME_LIMIT_SECONDS + NETWORK_BUFFER_SECONDS)
        is_correct = False
        if not is_timed_out and selected_option_id:
            is_correct = selected_option_id.strip().upper() == question.correct_option_id.strip().upper()

        # Update item attempt
        if idx < len(attempt.items):
            item = attempt.items[idx]
            item.submitted_at = now
            item.selected_option_id = selected_option_id
            item.is_correct = is_correct
            item.timed_out = is_timed_out

        attempt.current_question_index += 1

        if attempt.current_question_index >= len(attempt.assigned_question_ids):
            # All questions finished
            attempt.is_completed = True
            attempt.completed_at = now
            await QuizService._finalize_attempt(attempt)
            await attempt.save()
            return {
                "is_completed": True,
                "overall_score_percentage": attempt.overall_score_percentage,
                "message": "Diagnostic assessment complete.",
            }

        await attempt.save()
        return {
            "is_completed": False,
            "next_index": attempt.current_question_index,
            "total_questions": len(attempt.assigned_question_ids),
        }

    @staticmethod
    async def resume_attempt(attempt_id: PydanticObjectId, user_id: PydanticObjectId) -> Dict[str, any]:
        """
        Handles attempt resumption according to Phase 0.2 patched decisions:
          - Max 2 resumes allowed.
          - Resume 1: Fresh 60s timer for the currently active question.
          - Resume 2: Times out the currently active question (score 0), advances to next.
          - Resume > 2: Rejected with 400 Bad Request.
        """
        attempt = await QuizAttempt.get(attempt_id)
        if not attempt or attempt.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        if attempt.is_completed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt is already completed.")

        now = datetime.now(timezone.utc)
        expires_utc = _ensure_utc(attempt.expires_at)
        if expires_utc and now > expires_utc:
            attempt.is_completed = True
            await attempt.save()
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Attempt has expired.")

        attempt.resume_count += 1
        if attempt.resume_count > attempt.max_resumes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum resume attempts (2) exceeded for this diagnostic.",
            )

        if attempt.resume_count == 1:
            # 1st resume: fresh timer for current question
            if attempt.current_question_index < len(attempt.items):
                attempt.items[attempt.current_question_index].served_at = now
            await attempt.save()
            return {
                "resumed": True,
                "resume_count": attempt.resume_count,
                "message": "Resumed attempt. Fresh 60-second timer granted for current question.",
            }
        else:
            # 2nd resume: times out current question with 0 score and advances
            idx = attempt.current_question_index
            if idx < len(attempt.items):
                attempt.items[idx].timed_out = True
                attempt.items[idx].is_correct = False
                attempt.items[idx].submitted_at = now

            attempt.current_question_index += 1
            if attempt.current_question_index >= len(attempt.assigned_question_ids):
                attempt.is_completed = True
                attempt.completed_at = now
                await QuizService._finalize_attempt(attempt)

            await attempt.save()
            return {
                "resumed": True,
                "resume_count": attempt.resume_count,
                "message": "Second resume limit: current question timed out and advanced to next.",
            }

    @staticmethod
    async def record_tab_switch(attempt_id: PydanticObjectId, user_id: PydanticObjectId) -> Dict[str, any]:
        """
        Anti-cheat mechanism: increments tab_switch_count. If > 3, terminates attempt
        with auto_submitted_due_to_violations = True, excluding it from skill updates.
        """
        attempt = await QuizAttempt.get(attempt_id)
        if not attempt or attempt.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

        if attempt.is_completed:
            return {"tab_switch_count": attempt.tab_switch_count, "is_completed": True}

        attempt.tab_switch_count += 1
        is_terminated = False

        if attempt.tab_switch_count > 3:
            attempt.auto_submitted_due_to_violations = True
            attempt.is_completed = True
            attempt.completed_at = datetime.now(timezone.utc)
            is_terminated = True

        await attempt.save()
        return {
            "tab_switch_count": attempt.tab_switch_count,
            "auto_submitted_due_to_violations": is_terminated,
            "message": (
                "Maximum tab switches exceeded. Attempt terminated for integrity violations."
                if is_terminated
                else f"Warning: Tab switch recorded ({attempt.tab_switch_count}/3 allowed)."
            ),
        }

    @staticmethod
    async def _finalize_attempt(attempt: QuizAttempt) -> None:
        """
        Computes Bayesian shrinkage scores per topic and persists SkillProfile and SkillSnapshots.
        Formula: S = 100 * (sum(w_i * y_i) + m * mu) / (sum(w_i) + m)
        Excluded if auto_submitted_due_to_violations == True.
        """
        if attempt.auto_submitted_due_to_violations:
            attempt.overall_score_percentage = 0.0
            logger.warning("Attempt %s auto-submitted due to violations; excluded from skill profile.", attempt.id)
            return

        # Fetch questions to inspect topics and difficulty weights
        questions_map: Dict[PydanticObjectId, Question] = {}
        for q_id in attempt.assigned_question_ids:
            q = await Question.get(q_id)
            if q:
                questions_map[q.id] = q

        topic_stats: Dict[str, Dict[str, float]] = {}
        total_correct = 0
        total_scored_items = 0

        for item in attempt.items:
            q = questions_map.get(item.question_id)
            if not q or q.repeat_exposure:
                # Exclude repeat exposure questions from scoring weight
                continue

            topic = q.topic_slug
            if topic not in topic_stats:
                topic_stats[topic] = {"weighted_correct": 0.0, "total_weight": 0.0}

            w = DIFFICULTY_WEIGHTS.get(q.difficulty, 1.0)
            y = 1.0 if item.is_correct else 0.0

            topic_stats[topic]["weighted_correct"] += (w * y)
            topic_stats[topic]["total_weight"] += w

            if item.is_correct:
                total_correct += 1
            total_scored_items += 1

        # Calculate Bayesian shrinkage score for each topic
        m = DEFAULT_SHRINKAGE_M
        mu = DEFAULT_PRIOR_MU
        now = datetime.now(timezone.utc)

        skill_profile = await SkillProfile.find_one(SkillProfile.user_id == attempt.user_id)
        if not skill_profile:
            skill_profile = SkillProfile(user_id=attempt.user_id)

        if attempt.subject_slug not in skill_profile.subjects:
            skill_profile.subjects[attempt.subject_slug] = {}

        for topic, stats in topic_stats.items():
            num = stats["weighted_correct"] + (m * mu)
            den = stats["total_weight"] + m
            bayesian_score = round(100.0 * (num / den), 2)

            prior_skill = skill_profile.subjects[attempt.subject_slug].get(topic)
            prior_count = prior_skill.diagnostic_attempts_count if prior_skill else 0

            skill_profile.subjects[attempt.subject_slug][topic] = TopicSkill(
                overall_score=bayesian_score,
                confidence_level="medium" if stats["total_weight"] >= 4.0 else "low",
                last_assessed_at=now,
                diagnostic_attempts_count=prior_count + 1,
            )

            # Record SkillSnapshot for multi-session trend tracking
            snapshot = SkillSnapshot(
                user_id=attempt.user_id,
                subject_slug=attempt.subject_slug,
                topic_slug=topic,
                score=bayesian_score,
                source_type="diagnostic",
                source_id=attempt.id,
                recorded_at=now,
            )
            await snapshot.insert()

        skill_profile.last_diagnostic_at[attempt.subject_slug] = now
        skill_profile.updated_at = now
        await skill_profile.save()

        # Overall attempt score percentage
        overall_pct = (total_correct / max(1, total_scored_items)) * 100.0
        attempt.overall_score_percentage = round(overall_pct, 2)
