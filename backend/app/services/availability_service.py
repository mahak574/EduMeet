import zoneinfo
from datetime import date, datetime, time, timedelta, timezone
from typing import Tuple


def local_minutes_to_utc_interval(
    local_date: date,
    start_min: int,
    end_min: int,
    tz_name: str = "UTC",
) -> Tuple[datetime, datetime]:
    """
    Expands a local half-open interval [start_min, end_min) on local_date into UTC datetimes.
    Handles DST transitions (spring-forward gap and fall-back overlap) via round-trip verification:
      - Nonexistent (spring-forward gap): detected when round-trip local -> UTC -> local does not match.
        Advanced to the next valid local wall-clock minute.
      - Ambiguous (fall-back overlap): detected when fold=0 and fold=1 produce different UTC times.
        Explicitly binds fold=0 (first occurrence) by convention.
    """
    tz = zoneinfo.ZoneInfo(tz_name)

    def _convert_minute(target_min: int) -> datetime:
        # End minute can be up to 1440 (midnight end of day)
        days_offset = target_min // 1440
        min_in_day = target_min % 1440

        curr_date = local_date + timedelta(days=days_offset)
        hour = min_in_day // 60
        minute = min_in_day % 60

        naive_dt = datetime.combine(curr_date, time(hour, minute))
        dt_aware = naive_dt.replace(tzinfo=tz, fold=0)
        utc_dt = dt_aware.astimezone(timezone.utc)
        round_trip_local = utc_dt.astimezone(tz)

        # 1. Check for nonexistent time (spring-forward gap) via round-trip conversion:
        # In a gap, round-trip returns a shifted local wall-clock time because the time does not exist.
        if round_trip_local.hour != hour or round_trip_local.minute != minute:
            # Advance to the first valid wall-clock minute at the transition boundary (e.g. 03:00 EDT)
            first_valid_local = round_trip_local.replace(minute=0, second=0, microsecond=0)
            return first_valid_local.astimezone(timezone.utc)

        # 2. Check for ambiguity (fall-back overlap):
        # The local time exists, but fold=0 and fold=1 produce different UTC times.
        # Fall-back rule: use fold=0 (first occurrence / daylight saving time) by convention.
        dt_fold1 = naive_dt.replace(tzinfo=tz, fold=1)
        if dt_aware.astimezone(timezone.utc) != dt_fold1.astimezone(timezone.utc):
            return dt_aware.astimezone(timezone.utc)

        return utc_dt

    utc_start = _convert_minute(start_min)
    utc_end = _convert_minute(end_min)
    return utc_start, utc_end


def expand_and_merge_slots(
    slots_local: list[tuple[date, int, int]],
    tz_name: str = "UTC",
) -> list[Tuple[datetime, datetime]]:
    """
    Expands recurring local slots to UTC, drops empty slots from DST gaps,
    and merges adjacent or overlapping contiguous segments.
    """
    expanded: list[Tuple[datetime, datetime]] = []
    for local_date, s_min, e_min in slots_local:
        start_utc, end_utc = local_minutes_to_utc_interval(local_date, s_min, e_min, tz_name)
        # Drop empty slots (e.g. from DST spring-forward gaps)
        if end_utc > start_utc:
            expanded.append((start_utc, end_utc))

    if not expanded:
        return []

    # Sort intervals by start time
    expanded.sort(key=lambda x: x[0])

    merged: list[Tuple[datetime, datetime]] = [expanded[0]]
    for current_start, current_end in expanded[1:]:
        prev_start, prev_end = merged[-1]
        # If contiguous or overlapping, merge
        if current_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged


def compute_contiguous_overlap_minutes(
    intervals_a: list[Tuple[datetime, datetime]],
    intervals_b: list[Tuple[datetime, datetime]],
    min_continuous_minutes: int = 60,
) -> list[Tuple[datetime, datetime, int]]:
    """
    Computes pairwise contiguous overlap intervals between two users that satisfy
    the minimum required continuous duration (default >= 60 min, ideally 70 min).
    """
    valid_overlaps: list[Tuple[datetime, datetime, int]] = []

    for a_start, a_end in intervals_a:
        for b_start, b_end in intervals_b:
            overlap_start = max(a_start, b_start)
            overlap_end = min(a_end, b_end)

            if overlap_end > overlap_start:
                duration_mins = int((overlap_end - overlap_start).total_seconds() // 60)
                if duration_mins >= min_continuous_minutes:
                    valid_overlaps.append((overlap_start, overlap_end, duration_mins))

    return valid_overlaps

