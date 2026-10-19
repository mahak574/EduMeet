import pytest
from datetime import datetime, timezone
from beanie import PydanticObjectId
from fastapi import HTTPException

from app.models.consolidated import Block, Report, User
from app.schemas.safety import CreateReportRequest, ResolveReportRequest
from app.services.safety_service import SafetyService


@pytest.mark.asyncio
async def test_create_safety_report_and_block():
    reporter = User(
        email="reporter@university.edu",
        full_name="Alice Reporter",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
        subjects_studied=["dsa"],
    )
    await reporter.insert()

    bad_user = User(
        email="badactor@university.edu",
        full_name="Bob Troublesome",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        languages=["en"],
        subjects_studied=["dsa"],
    )
    await bad_user.insert()

    # Self-reporting must fail
    with pytest.raises(HTTPException) as exc_info:
        await SafetyService.create_report(
            reporter,
            CreateReportRequest(
                reported_user_id=reporter.id,
                reason="harassment",
                details="Testing self report which must be rejected.",
            ),
        )
    assert exc_info.value.status_code == 400

    # Valid report with auto-block
    report_res = await SafetyService.create_report(
        reporter,
        CreateReportRequest(
            reported_user_id=bad_user.id,
            reason="harassment",
            details="Used offensive language repeatedly during the peer segment.",
            block_user=True,
        ),
    )
    assert report_res.status == "pending"
    assert report_res.reported_user_id == bad_user.id

    # Verify mutual exclusion block was created
    is_blocked = await SafetyService.is_blocked_mutually(reporter.id, bad_user.id)
    assert is_blocked is True

    # Check block list
    blocks = await SafetyService.list_blocks(reporter.id)
    assert len(blocks) == 1
    assert blocks[0].blocked_user_id == bad_user.id

    # Unblock
    unblocked = await SafetyService.unblock_user(reporter.id, bad_user.id)
    assert unblocked is True
    is_blocked_after = await SafetyService.is_blocked_mutually(reporter.id, bad_user.id)
    assert is_blocked_after is False


@pytest.mark.asyncio
async def test_admin_report_resolution_and_ban():
    admin = User(
        email="admin@edumeet.org",
        full_name="Admin Moderator",
        role="admin",
        age_confirmed=True,
        country="US",
        timezone="UTC",
    )
    await admin.insert()

    reported_user = User(
        email="spammer@university.edu",
        full_name="Spam Bot",
        age_confirmed=True,
        country="US",
        timezone="UTC",
        is_active=True,
        is_blocked=False,
    )
    await reported_user.insert()

    report = Report(
        reporter_user_id=PydanticObjectId(),
        reported_user_id=reported_user.id,
        reason="spam",
        details="Spamming commercial links in session whiteboard.",
        status="pending",
    )
    await report.insert()

    # Resolve report as banned
    resolved = await SafetyService.resolve_report(
        report.id,
        admin,
        ResolveReportRequest(status="banned", resolution_notes="Confirmed commercial spam violation."),
    )
    assert resolved.status == "banned"
    assert resolved.resolved_by == str(admin.id)

    # Check that user account is deactivated
    refreshed_user = await User.get(reported_user.id)
    assert refreshed_user.is_blocked is True
    assert refreshed_user.is_active is False
