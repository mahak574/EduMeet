from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_admin, get_current_user
from app.models.consolidated import User
from app.schemas.common import APIResponse
from app.schemas.safety import (
    BlockResponse,
    BlockUserRequest,
    CreateReportRequest,
    ReportResponse,
    ResolveReportRequest,
)
from app.services.safety_service import SafetyService

router = APIRouter(prefix="/safety", tags=["Safety & Moderation"])


@router.post("/reports", response_model=APIResponse[ReportResponse], status_code=status.HTTP_201_CREATED)
async def create_safety_report(
    data: CreateReportRequest,
    current_user: User = Depends(get_current_user),
):
    report = await SafetyService.create_report(current_user, data)
    return APIResponse(
        success=True,
        message="Your report has been submitted to Trust & Safety for immediate review.",
        data=report,
    )


@router.get("/reports", response_model=APIResponse[List[ReportResponse]])
async def list_safety_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: User = Depends(get_current_admin),
):
    reports = await SafetyService.list_reports(status_filter=status_filter, skip=skip, limit=limit)
    return APIResponse(success=True, data=reports)


@router.patch("/reports/{report_id}", response_model=APIResponse[ReportResponse])
async def resolve_safety_report(
    report_id: PydanticObjectId,
    data: ResolveReportRequest,
    admin_user: User = Depends(get_current_admin),
):
    updated = await SafetyService.resolve_report(report_id, admin_user, data)
    return APIResponse(
        success=True,
        message=f"Report marked as {data.status}.",
        data=updated,
    )


@router.post("/blocks", response_model=APIResponse[BlockResponse], status_code=status.HTTP_201_CREATED)
async def block_user(
    data: BlockUserRequest,
    current_user: User = Depends(get_current_user),
):
    block = await SafetyService.block_user(current_user.id, data.blocked_user_id)
    return APIResponse(
        success=True,
        message="User successfully blocked. You will never be matched with this participant.",
        data=block,
    )


@router.delete("/blocks/{blocked_user_id}", response_model=APIResponse[dict])
async def unblock_user(
    blocked_user_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    unblocked = await SafetyService.unblock_user(current_user.id, blocked_user_id)
    if not unblocked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block record not found.")
    return APIResponse(success=True, message="User unblocked successfully.", data={"unblocked": True})


@router.get("/blocks", response_model=APIResponse[List[BlockResponse]])
async def list_blocks(
    current_user: User = Depends(get_current_user),
):
    blocks = await SafetyService.list_blocks(current_user.id)
    return APIResponse(success=True, data=blocks)
