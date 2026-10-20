import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.config import settings
from app.models.consolidated import (
    Question,
    QuizAttempt,
    Session,
    SessionParticipant,
    SkillProfile,
    SkillSnapshot,
    User,
)

logger = logging.getLogger(__name__)

PHASE_DURATIONS_MINUTES = {
    "waiting_room": 5,
    "teacher_a": 25,
    "teacher_b": 25,
    "quiz_exchange": 10,
    "followup": 60,
    "closed": 0,
}

PHASE_SEQUENCE = [
    "waiting_room",
    "teacher_a",
    "teacher_b",
    "quiz_exchange",
    "followup",
    "closed",
]


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SessionService:
    @classmethod
    async def get_session(cls, session_id: PydanticObjectId) -> Session:
        session = await Session.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        return session

    @classmethod
    async def get_user_sessions(cls, user_id: PydanticObjectId) -> List[Dict[str, Any]]:
        sessions = await Session.find(
            {"participants.user_id": user_id}
        ).sort("-scheduled_start_utc").to_list()

        results = []
        for s in sessions:
            user_p = next((p for p in s.participants if p.user_id == user_id), None)
            partner_p = next((p for p in s.participants if p.user_id != user_id), None)
            partner_user = await User.get(partner_p.user_id) if partner_p else None
            results.append({
                "session_id": str(s.id),
                "status": s.status,
                "session_mode": s.session_mode,
                "my_role": user_p.role if user_p else "teacher_a",
                "my_teach_subject": user_p.teach_subject_slug if user_p else "",
                "my_teach_topic": user_p.teach_topic_slug if user_p else "",
                "my_learn_subject": user_p.learn_subject_slug if user_p else "",
                "my_learn_topic": user_p.learn_topic_slug if user_p else "",
                "partner_name": partner_user.full_name if partner_user else "Peer Student",
                "scheduled_start_utc": s.scheduled_start_utc.isoformat() if s.scheduled_start_utc else "",
                "scheduled_end_utc": s.scheduled_end_utc.isoformat() if s.scheduled_end_utc else "",
            })
        return results

    @classmethod
    async def create_demo_session(cls, user_id: PydanticObjectId, subject: Optional[str] = None) -> Session:
        # Determine subjects dynamically based on current user's profile
        current_user = await User.get(user_id)
        if not current_user or not current_user.age_confirmed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Age confirmation is required before creating a session.",
            )
        studied = current_user.subjects_studied if current_user.subjects_studied else []
        teach_sub = subject or (studied[0] if studied else "maths")
        learn_sub = studied[1] if len(studied) > 1 else ("python" if teach_sub != "python" else "physics")

        # Find or create a demo peer
        peer = await User.find_one(User.email == "demo_peer@edumeet.org")
        if not peer:
            peer = User(
                email="demo_peer@edumeet.org",
                full_name="Jordan (Peer Mentor)",
                age_confirmed=True,
                country="US",
                timezone="UTC",
                role="student",
                subjects_studied=[teach_sub, learn_sub],
            )
            await peer.insert()

        now = datetime.now(timezone.utc)
        session = Session(
            match_id=PydanticObjectId(),
            session_mode="regular_30_30",
            status="waiting_room",
            scheduled_start_utc=now,
            scheduled_end_utc=now + timedelta(minutes=60),
            phase_ends_at=now + timedelta(minutes=25),
            video_room_id=f"edumeet-demo-{user_id}",
            yjs_doc_id=f"edumeet-doc-{user_id}",
            participants=[
                SessionParticipant(
                    user_id=user_id,
                    role="teacher_a",
                    teach_subject_slug=teach_sub,
                    teach_topic_slug=f"{teach_sub}-core-concepts",
                    learn_subject_slug=learn_sub,
                    learn_topic_slug=f"{learn_sub}-core-concepts",
                ),
                SessionParticipant(
                    user_id=peer.id,
                    role="teacher_b",
                    teach_subject_slug=learn_sub,
                    teach_topic_slug=f"{learn_sub}-core-concepts",
                    learn_subject_slug=teach_sub,
                    learn_topic_slug=f"{teach_sub}-core-concepts",
                ),
            ],
            present_user_ids=[user_id, peer.id],
        )
        await session.insert()
        return session

    @classmethod
    async def get_session_details(
        cls, session_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> Dict[str, Any]:
        session = await cls.get_session(session_id)

        # Check membership
        user_p = next((p for p in session.participants if p.user_id == user_id), None)
        partner_p = next((p for p in session.participants if p.user_id != user_id), None)

        if not user_p or not partner_p:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a registered participant in this session.",
            )

        now = datetime.now(timezone.utc)
        phase_ends_utc = _ensure_utc(session.phase_ends_at)

        # Calculate server-authoritative remaining seconds
        remaining_seconds = 0
        if phase_ends_utc:
            if session.is_paused and session.paused_at:
                paused_at_utc = _ensure_utc(session.paused_at)
                remaining_seconds = max(0, int((phase_ends_utc - paused_at_utc).total_seconds()))
            else:
                remaining_seconds = max(0, int((phase_ends_utc - now).total_seconds()))

        partner_user = await User.get(partner_p.user_id)
        partner_name = partner_user.full_name if partner_user else "Peer Student"

        # Determine who is actively teaching
        current_teacher_id = None
        if session.status == "teacher_a":
            p_a = next((p for p in session.participants if p.role == "teacher_a"), None)
            current_teacher_id = str(p_a.user_id) if p_a else None
        elif session.status == "teacher_b":
            p_b = next((p for p in session.participants if p.role == "teacher_b"), None)
            current_teacher_id = str(p_b.user_id) if p_b else None

        is_current_teacher = current_teacher_id == str(user_id)

        return {
            "session_id": str(session.id),
            "status": session.status,
            "session_mode": session.session_mode,
            "my_role": user_p.role,
            "my_teach_subject": user_p.teach_subject_slug,
            "my_teach_topic": user_p.teach_topic_slug,
            "my_learn_subject": user_p.learn_subject_slug,
            "my_learn_topic": user_p.learn_topic_slug,
            "partner_id": str(partner_p.user_id),
            "partner_name": partner_name,
            "partner_role": partner_p.role,
            "partner_teach_topic": partner_p.teach_topic_slug,
            "current_teacher_id": current_teacher_id,
            "is_current_teacher": is_current_teacher,
            "scheduled_start_utc": session.scheduled_start_utc,
            "scheduled_end_utc": session.scheduled_end_utc,
            "phase_ends_at": session.phase_ends_at,
            "remaining_seconds": remaining_seconds,
            "is_paused": session.is_paused,
            "total_paused_seconds": session.total_paused_seconds,
            "present_user_ids": [str(uid) for uid in session.present_user_ids],
            "video_room_id": session.video_room_id,
            "yjs_doc_id": session.yjs_doc_id,
            "chat_is_locked": session.chat_is_locked,
        }

    @classmethod
    async def advance_phase(
        cls,
        session_id: PydanticObjectId,
        target_phase: Optional[str] = None,
    ) -> Session:
        session = await cls.get_session(session_id)
        current_idx = PHASE_SEQUENCE.index(session.status) if session.status in PHASE_SEQUENCE else 0

        if target_phase:
            if target_phase not in PHASE_SEQUENCE:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target phase.")
            next_phase = target_phase
        else:
            if current_idx >= len(PHASE_SEQUENCE) - 1:
                return session
            next_phase = PHASE_SEQUENCE[current_idx + 1]

        now = datetime.now(timezone.utc)
        duration_mins = PHASE_DURATIONS_MINUTES.get(next_phase, 0)

        session.status = next_phase
        session.phase_ends_at = now + timedelta(minutes=duration_mins) if duration_mins > 0 else None
        session.is_paused = False
        session.paused_at = None

        if next_phase == "teacher_a" and not session.actual_start_utc:
            session.actual_start_utc = now
        elif next_phase == "closed":
            session.actual_end_utc = now
            session.chat_is_locked = True
            session.chat_locked_at = now

        await session.save()
        logger.info("Session %s advanced to phase '%s' (ends at: %s)", session.id, next_phase, session.phase_ends_at)
        return session

    @classmethod
    async def handle_user_connected(
        cls, session_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> Tuple[Session, Optional[str]]:
        """
        Records user presence.
        In waiting_room, triggers atomic transition to teacher_a when both are connected.
        Resumes session timer if it was paused due to disconnect grace.
        """
        session = await cls.get_session(session_id)
        now = datetime.now(timezone.utc)
        event_type: Optional[str] = None

        # Add to present users list
        if user_id not in session.present_user_ids:
            session.present_user_ids.append(user_id)

        # Case 1: Waiting Room auto-start when both are present
        all_participant_ids = [p.user_id for p in session.participants]
        if session.status == "waiting_room":
            both_present = all(p_id in session.present_user_ids for p_id in all_participant_ids)
            if both_present:
                session.status = "teacher_a"
                session.actual_start_utc = now
                session.phase_ends_at = now + timedelta(minutes=PHASE_DURATIONS_MINUTES["teacher_a"])
                event_type = "PHASE_TRANSITION"

        # Case 2: Reconnection from disconnect grace pause
        elif session.is_paused and session.paused_at:
            paused_at_utc = _ensure_utc(session.paused_at)
            pause_duration = now - paused_at_utc
            pause_seconds = int(pause_duration.total_seconds())

            session.total_paused_seconds += pause_seconds
            if session.phase_ends_at:
                phase_ends_utc = _ensure_utc(session.phase_ends_at)
                session.phase_ends_at = phase_ends_utc + pause_duration

            session.is_paused = False
            session.paused_at = None
            event_type = "SESSION_RESUMED"

        await session.save()
        return session, event_type

    @classmethod
    async def handle_user_disconnected(
        cls, session_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> Tuple[Session, bool]:
        """
        Removes user from presence.
        If an active session drops to < 2 users, pauses session within disconnect grace cap (10 min).
        """
        session = await cls.get_session(session_id)
        now = datetime.now(timezone.utc)
        was_paused = False

        if user_id in session.present_user_ids:
            session.present_user_ids.remove(user_id)

        active_phases = ["teacher_a", "teacher_b", "quiz_exchange"]
        if session.status in active_phases and len(session.present_user_ids) < 2:
            if session.total_paused_seconds < session.max_pause_cap_seconds:
                session.is_paused = True
                session.paused_at = now
                was_paused = True

        await session.save()
        return session, was_paused

    @classmethod
    async def get_precheck_questions(
        cls, session_id: PydanticObjectId, user_id: PydanticObjectId
    ) -> List[Dict[str, Any]]:
        """
        Returns 3-4 held-out diagnostic check items for the student's learning topic.
        Strictly excludes questions previously served to the user during diagnostic attempts.
        """
        session = await cls.get_session(session_id)
        user_p = next((p for p in session.participants if p.user_id == user_id), None)
        if not user_p:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

        # Find all questions served in user's prior diagnostic attempts
        past_attempts = await QuizAttempt.find(QuizAttempt.user_id == user_id).to_list()
        served_q_ids = set()
        for att in past_attempts:
            served_q_ids.update(att.served_question_ids)

        # Query approved questions for the student's learning topic
        available_qs = await Question.find({
            "subject_slug": user_p.learn_subject_slug,
            "topic_slug": user_p.learn_topic_slug,
            "review_status": "approved",
        }).to_list()

        # Exclude previously served questions
        unserved = [q for q in available_qs if q.id not in served_q_ids]
        selected_qs = unserved[:3] if len(unserved) >= 3 else available_qs[:3]

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
    async def submit_precheck(
        cls,
        session_id: PydanticObjectId,
        user_id: PydanticObjectId,
        answers: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Grades pre-check items and creates a SkillSnapshot baseline.
        """
        session = await cls.get_session(session_id)
        user_p = next((p for p in session.participants if p.user_id == user_id), None)
        if not user_p:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participant not found.")

        total = len(answers)
        correct_count = 0

        for q_id_str, selected_opt in answers.items():
            try:
                q = await Question.get(PydanticObjectId(q_id_str))
                if q and q.correct_option_id == selected_opt:
                    correct_count += 1
            except Exception:
                continue

        score_pct = round((correct_count / max(1, total)) * 100.0, 1)

        # Record pre-session baseline snapshot
        snapshot = SkillSnapshot(
            user_id=user_id,
            subject_slug=user_p.learn_subject_slug,
            topic_slug=user_p.learn_topic_slug,
            score=score_pct,
            source_type="pre_session",
            source_id=session.id,
        )
        await snapshot.insert()
        user_p.pre_session_snapshot_id = snapshot.id
        await session.save()

        return {
            "session_id": str(session.id),
            "score_percentage": score_pct,
            "correct_count": correct_count,
            "total_questions": total,
            "snapshot_id": str(snapshot.id),
        }
