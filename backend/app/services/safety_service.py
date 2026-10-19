import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.consolidated import Block, Report, TelemetryEvent, User
from app.schemas.safety import BlockResponse, CreateReportRequest, ReportResponse, ResolveReportRequest

logger = logging.getLogger(__name__)


class SafetyService:
    @classmethod
    async def create_report(
        cls,
        reporter: User,
        data: CreateReportRequest,
    ) -> ReportResponse:
        if reporter.id == data.reported_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot file a Trust & Safety report against yourself.",
            )

        reported_user = await User.get(data.reported_user_id)
        if not reported_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported user does not exist.",
            )

        report = Report(
            reporter_user_id=reporter.id,
            reported_user_id=data.reported_user_id,
            session_id=data.session_id,
            reason=data.reason,
            details=data.details.strip(),
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        await report.insert()

        if data.block_user:
            await cls.block_user(reporter.id, data.reported_user_id)

        # Audit telemetry event
        await TelemetryEvent(
            user_id=reporter.id,
            event_name="safety_report_filed",
            payload={
                "report_id": str(report.id),
                "reason": data.reason,
                "reported_user_id": str(data.reported_user_id),
                "session_id": str(data.session_id) if data.session_id else None,
            },
        ).insert()

        # Check threshold for rapid safety escalation
        pending_count = await Report.find(
            Report.reported_user_id == data.reported_user_id,
            Report.status == "pending",
        ).count()
        if pending_count >= 3:
            logger.warning(
                "CRITICAL TRUST & SAFETY ALERT: User %s has %d pending safety reports!",
                data.reported_user_id,
                pending_count,
            )

        return ReportResponse(
            id=report.id,
            reporter_user_id=report.reporter_user_id,
            reported_user_id=report.reported_user_id,
            session_id=report.session_id,
            reason=report.reason,
            details=report.details,
            status=report.status,
            resolution_notes=report.resolution_notes,
            resolved_by=report.resolved_by,
            created_at=report.created_at,
        )

    @classmethod
    async def list_reports(
        cls,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ReportResponse]:
        query = {}
        if status_filter:
            query["status"] = status_filter

        reports = await Report.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
        return [
            ReportResponse(
                id=r.id,
                reporter_user_id=r.reporter_user_id,
                reported_user_id=r.reported_user_id,
                session_id=r.session_id,
                reason=r.reason,
                details=r.details,
                status=r.status,
                resolution_notes=r.resolution_notes,
                resolved_by=r.resolved_by,
                created_at=r.created_at,
            )
            for r in reports
        ]

    @classmethod
    async def resolve_report(
        cls,
        report_id: PydanticObjectId,
        admin_user: User,
        data: ResolveReportRequest,
    ) -> ReportResponse:
        report = await Report.get(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found.",
            )

        report.status = data.status
        report.resolution_notes = data.resolution_notes
        report.resolved_by = str(admin_user.id)
        await report.save()

        # If banned, deactivate and block the reported user account
        if data.status == "banned":
            reported_user = await User.get(report.reported_user_id)
            if reported_user:
                reported_user.is_blocked = True
                reported_user.is_active = False
                await reported_user.save()
                logger.info(
                    "User %s has been banned following resolution of report %s.",
                    reported_user.id,
                    report.id,
                )

        return ReportResponse(
            id=report.id,
            reporter_user_id=report.reporter_user_id,
            reported_user_id=report.reported_user_id,
            session_id=report.session_id,
            reason=report.reason,
            details=report.details,
            status=report.status,
            resolution_notes=report.resolution_notes,
            resolved_by=report.resolved_by,
            created_at=report.created_at,
        )

    @classmethod
    async def block_user(
        cls,
        blocker_id: PydanticObjectId,
        blocked_id: PydanticObjectId,
    ) -> BlockResponse:
        if blocker_id == blocked_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot block yourself.",
            )

        blocked_user = await User.get(blocked_id)
        if not blocked_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user to block not found.",
            )

        existing = await Block.find_one(
            Block.blocker_user_id == blocker_id,
            Block.blocked_user_id == blocked_id,
        )
        if not existing:
            block = Block(
                blocker_user_id=blocker_id,
                blocked_user_id=blocked_id,
                created_at=datetime.now(timezone.utc),
            )
            await block.insert()
        else:
            block = existing

        return BlockResponse(
            id=block.id,
            blocker_user_id=block.blocker_user_id,
            blocked_user_id=block.blocked_user_id,
            blocked_user_name=blocked_user.full_name,
            created_at=block.created_at,
        )

    @classmethod
    async def unblock_user(
        cls,
        blocker_id: PydanticObjectId,
        blocked_id: PydanticObjectId,
    ) -> bool:
        result = await Block.find(
            Block.blocker_user_id == blocker_id,
            Block.blocked_user_id == blocked_id,
        ).delete()
        return result.deleted_count > 0

    @classmethod
    async def list_blocks(cls, user_id: PydanticObjectId) -> List[BlockResponse]:
        blocks = await Block.find(Block.blocker_user_id == user_id).to_list()
        res = []
        for b in blocks:
            target = await User.get(b.blocked_user_id)
            res.append(
                BlockResponse(
                    id=b.id,
                    blocker_user_id=b.blocker_user_id,
                    blocked_user_id=b.blocked_user_id,
                    blocked_user_name=target.full_name if target else "Unknown User",
                    created_at=b.created_at,
                )
            )
        return res

    @classmethod
    async def is_blocked_mutually(
        cls,
        user_a_id: PydanticObjectId,
        user_b_id: PydanticObjectId,
    ) -> bool:
        blocked = await Block.find_one({
            "$or": [
                {"blocker_user_id": user_a_id, "blocked_user_id": user_b_id},
                {"blocker_user_id": user_b_id, "blocked_user_id": user_a_id},
            ]
        })
        return blocked is not None
