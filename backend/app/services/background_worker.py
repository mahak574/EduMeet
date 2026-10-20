import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from beanie import PydanticObjectId

from app.config import settings
from app.models.consolidated import Message, Session, User
from app.services.matching_service import MatchingService
from app.services.ws_session_manager import ws_manager

logger = logging.getLogger(__name__)

# Next phase mapping and standard phase durations
PHASE_FLOW = {
    "teaching_part_1": ("break_5min", 5),
    "break_5min": ("teaching_part_2", 25),
    "teaching_part_2": ("followup_5min", 5),
    "followup_5min": ("completed", 0),
}


class BackgroundWorker:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running: bool = False

    def start(self):
        """Starts the APScheduler background worker jobs."""
        if self._is_running:
            return

        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)

        # 1. Phase transitions every 10 seconds
        self.scheduler.add_job(
            self.transition_session_phases,
            "interval",
            seconds=10,
            id="session_phase_transitions",
            replace_existing=True,
        )

        # 2. No-show cancellation every 30 seconds
        self.scheduler.add_job(
            self.cancel_no_show_sessions,
            "interval",
            seconds=30,
            id="no_show_cancellation",
            replace_existing=True,
        )

        # 3. Hourly matching cycle
        self.scheduler.add_job(
            self.run_hourly_matching,
            "interval",
            hours=1,
            id="hourly_matching",
            replace_existing=True,
        )

        # 4. Session reminders every 5 minutes
        self.scheduler.add_job(
            self.send_session_reminders,
            "interval",
            minutes=5,
            id="session_reminders",
            replace_existing=True,
        )

        # 5. Post-check reminders every 5 minutes
        self.scheduler.add_job(
            self.send_post_check_reminders,
            "interval",
            minutes=5,
            id="post_check_reminders",
            replace_existing=True,
        )

        # 6. Daily chat purge (messages for completed/cancelled sessions older than 30 days)
        self.scheduler.add_job(
            self.purge_expired_chat,
            "interval",
            hours=24,
            id="chat_purge",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        logger.info("EduMeet APScheduler BackgroundWorker successfully started.")

    def stop(self):
        """Stops the APScheduler background worker."""
        if self.scheduler and self._is_running:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception as e:
                logger.warning("Error shutting down BackgroundWorker scheduler: %s", e)
            self._is_running = False
            logger.info("EduMeet APScheduler BackgroundWorker stopped.")

    @classmethod
    async def transition_session_phases(cls):
        """
        Scans sessions whose phase has elapsed and advances to the next phase
        with exactly ONE atomic find_one_and_update per transition.
        """
        now = datetime.now(timezone.utc)
        coll = Session.get_motor_collection()

        # Find sessions needing phase transition
        query = {
            "status": {"$in": list(PHASE_FLOW.keys())},
            "phase_ends_at": {"$lte": now},
        }

        cursor = coll.find(query)
        sessions_to_advance = await cursor.to_list(length=100)

        for sess_doc in sessions_to_advance:
            current_status = sess_doc["status"]
            next_status, duration_mins = PHASE_FLOW.get(current_status, (None, None))
            if not next_status:
                continue

            next_ends_at = now + timedelta(minutes=duration_mins) if duration_mins > 0 else None
            update_fields = {
                "status": next_status,
                "phase_ends_at": next_ends_at,
                "updated_at": now,
            }
            if next_status == "completed":
                update_fields["completed_at"] = now

            # Perform atomic find_one_and_update per transition
            updated = await coll.find_one_and_update(
                {
                    "_id": sess_doc["_id"],
                    "status": current_status,
                    "phase_ends_at": {"$lte": now},
                },
                {"$set": update_fields},
                return_document=True,
            )

            if updated:
                sess_id_str = str(sess_doc["_id"])
                logger.info(
                    "BackgroundWorker: Session %s atomic phase transition: %s -> %s (phase_ends_at: %s)",
                    sess_id_str,
                    current_status,
                    next_status,
                    next_ends_at,
                )
                # Broadcast transition event to room participants
                await ws_manager.broadcast(
                    sess_id_str,
                    {
                        "type": "PHASE_TRANSITION",
                        "status": next_status,
                        "phase_ends_at": next_ends_at.isoformat() if next_ends_at else None,
                    },
                )

    @classmethod
    async def cancel_no_show_sessions(cls):
        """
        Cancels sessions at scheduled_start + 10 min if not started / fewer than 2 participants present.
        Increments no_show_count for absent users.
        """
        now = datetime.now(timezone.utc)
        coll = Session.get_motor_collection()
        cutoff = now - timedelta(minutes=10)

        query = {
            "status": "scheduled",
            "scheduled_start_utc": {"$lte": cutoff},
        }

        cursor = coll.find(query)
        stale_sessions = await cursor.to_list(length=50)

        for sess_doc in stale_sessions:
            # Atomic cancellation
            cancelled = await coll.find_one_and_update(
                {
                    "_id": sess_doc["_id"],
                    "status": "scheduled",
                    "scheduled_start_utc": {"$lte": cutoff},
                },
                {
                    "$set": {
                        "status": "cancelled",
                        "cancellation_reason": "No-show: Automatically cancelled after 10 minutes without mutual attendance.",
                        "updated_at": now,
                    }
                },
                return_document=True,
            )

            if cancelled:
                sess_id_str = str(sess_doc["_id"])
                logger.warning("BackgroundWorker: Cancelled no-show session %s", sess_id_str)
                # Identify absent participants and increment no_show_count
                present_ids = set(str(uid) for uid in sess_doc.get("present_user_ids", []))
                for p in sess_doc.get("participants", []):
                    p_uid_str = str(p.get("user_id"))
                    if p_uid_str not in present_ids:
                        await User.find({"_id": p.get("user_id")}).update(
                            {"$inc": {"no_show_count": 1}}
                        )
                        logger.info("Recorded no-show penalty for user %s", p_uid_str)

                # Broadcast cancellation
                await ws_manager.broadcast(
                    sess_id_str,
                    {
                        "type": "SESSION_CANCELLED",
                        "status": "cancelled",
                        "reason": "No-show timeout (10 minutes)",
                    },
                )

    @classmethod
    async def run_hourly_matching(cls):
        """Executes hourly bipartite matching cycle for waiting pool candidates."""
        logger.info("BackgroundWorker: Triggering hourly matching cycle...")
        try:
            matches = await MatchingService.run_matching_cycle()
            logger.info("BackgroundWorker: Hourly matching created %d matches.", len(matches))
        except Exception as exc:
            logger.error("BackgroundWorker: Hourly matching cycle failed: %s", exc)

    @classmethod
    async def send_session_reminders(cls):
        """Finds sessions starting in ~15 minutes and logs/dispatches reminders."""
        now = datetime.now(timezone.utc)
        window_start = now + timedelta(minutes=10)
        window_end = now + timedelta(minutes=20)

        upcoming = await Session.find(
            Session.status == "scheduled",
            Session.scheduled_start_utc >= window_start,
            Session.scheduled_start_utc <= window_end,
        ).to_list()

        for s in upcoming:
            logger.debug("BackgroundWorker: Reminder for upcoming session %s starting at %s", s.id, s.scheduled_start_utc)

    @classmethod
    async def send_post_check_reminders(cls):
        """Finds recently completed sessions to remind students about reviews & post-check."""
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(minutes=15)

        completed = await Session.find(
            Session.status == "completed",
            Session.completed_at >= recent_cutoff,
        ).to_list()

        for s in completed:
            logger.debug("BackgroundWorker: Post-check reminder for completed session %s", s.id)

    @classmethod
    async def purge_expired_chat(cls):
        """Purges chat messages for sessions completed or cancelled > 30 days ago."""
        now = datetime.now(timezone.utc)
        purge_cutoff = now - timedelta(days=30)
        coll_session = Session.get_motor_collection()
        coll_messages = Message.get_motor_collection()

        old_sessions = await coll_session.find(
            {
                "status": {"$in": ["completed", "cancelled"]},
                "updated_at": {"$lte": purge_cutoff},
            },
            {"_id": 1},
        ).to_list(length=500)

        if old_sessions:
            sess_ids = [s["_id"] for s in old_sessions]
            res = await coll_messages.delete_many({"session_id": {"$in": sess_ids}})
            logger.info("BackgroundWorker: Purged %d chat messages for sessions older than 30 days.", res.deleted_count)


background_worker = BackgroundWorker()
