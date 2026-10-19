import pytest
from datetime import date, timezone
from app.models.consolidated import RecurringLocalSlot
from app.services.availability_service import local_minutes_to_utc_interval


def test_recurring_local_slot_validation():
    # Valid half-open interval: 09:00 to 10:00
    slot = RecurringLocalSlot(day_of_week=0, start_min=540, end_min=600)
    assert slot.start_min == 540
    assert slot.end_min == 600
    assert slot.start_time_str == "09:00"
    assert slot.end_time_str == "10:00"

    # Invalid: start >= end must raise ValueError
    with pytest.raises(ValueError):
        RecurringLocalSlot(day_of_week=0, start_min=600, end_min=540)

    with pytest.raises(ValueError):
        RecurringLocalSlot(day_of_week=0, start_min=600, end_min=600)

    # Valid: full day up to 1440
    slot_full = RecurringLocalSlot(day_of_week=5, start_min=0, end_min=1440)
    assert slot_full.end_min == 1440


def test_spring_forward_nonexistent_local_time():
    """
    In America/New_York on 2026-03-08, clocks jump from 02:00 to 03:00 EDT (UTC-4).
    The local time 02:30 (150 minutes since midnight) does not exist.
    Round-trip detection detects this and advances to the first valid local time (03:00 -> 07:00 UTC).
    """
    dst_date = date(2026, 3, 8)
    # 02:30 is 150 minutes; 03:30 is 210 minutes
    utc_start, utc_end = local_minutes_to_utc_interval(
        local_date=dst_date,
        start_min=150,
        end_min=210,
        tz_name="America/New_York",
    )

    # 02:30 does not exist, so it advances to 03:00 EDT = 07:00 UTC
    assert utc_start.hour == 7
    assert utc_start.minute == 0
    # 03:30 EDT = 07:30 UTC
    assert utc_end.hour == 7
    assert utc_end.minute == 30


def test_fall_back_ambiguous_local_time():
    """
    In America/New_York on 2026-11-01, clocks jump back from 02:00 to 01:00.
    The local time 01:30 occurs twice (EDT with UTC-4, and EST with UTC-5).
    By our rule, fold=0 (first occurrence / daylight time) is bound by convention.
    01:30 EDT (fold=0) = 05:30 UTC.
    """
    fall_back_date = date(2026, 11, 1)
    # 01:30 is 90 minutes; 02:30 is 150 minutes
    utc_start, utc_end = local_minutes_to_utc_interval(
        local_date=fall_back_date,
        start_min=90,
        end_min=150,
        tz_name="America/New_York",
    )

    # First occurrence of 01:30 is EDT (UTC-4), which translates to 05:30 UTC
    assert utc_start.hour == 5
    assert utc_start.minute == 30
    # 02:30 is after clocks fell back, so it is EST (UTC-5), translating to 07:30 UTC
    assert utc_end.hour == 7
    assert utc_end.minute == 30


def test_end_min_1440_converts_to_next_day():
    d = date(2026, 10, 20)
    utc_start, utc_end = local_minutes_to_utc_interval(d, 1320, 1440, "UTC")
    assert utc_start.day == 20
    assert utc_start.hour == 22
    assert utc_end.day == 21
    assert utc_end.hour == 0
    assert utc_end.minute == 0


def test_merge_adjacent_slots_and_overlap():
    from app.services.availability_service import (
        expand_and_merge_slots,
        compute_contiguous_overlap_minutes,
    )
    d1 = date(2026, 10, 20)
    d2 = date(2026, 10, 21)

    # User A: 20:00 to 24:00 on d1, and 00:00 to 02:00 on d2 (adjacent segments)
    slots_a = [(d1, 1200, 1440), (d2, 0, 120)]
    merged_a = expand_and_merge_slots(slots_a, "UTC")
    # Should merge into 1 continuous 6-hour segment: 20:00 to 02:00
    assert len(merged_a) == 1
    assert (merged_a[0][1] - merged_a[0][0]).total_seconds() == 6 * 3600

    # User B: 21:00 to 23:30 on d1 (2.5 hours = 150 minutes overlap with A)
    slots_b = [(d1, 1260, 1410)]
    merged_b = expand_and_merge_slots(slots_b, "UTC")

    overlaps = compute_contiguous_overlap_minutes(merged_a, merged_b, min_continuous_minutes=60)
    assert len(overlaps) == 1
    assert overlaps[0][2] == 150  # 150 contiguous minutes (>= 60 min)

