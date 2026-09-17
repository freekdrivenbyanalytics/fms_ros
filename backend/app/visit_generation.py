import calendar
from datetime import date, timedelta

OPEN_ENDED_HORIZON_DAYS = 90

_MONTHS_PER_UNIT = {"week": 0, "month": 1, "quarter": 3}


def add_calendar_months(d: date, months: int) -> date:
    """d stepped forward by `months` real calendar months, clamping the
    day-of-month to the target month's actual last day when it doesn't exist
    there (e.g. January 31 + 1 month -> February 28 or 29)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def step_occurrence(d: date, interval_unit: str, interval_count: int) -> date:
    if interval_unit == "week":
        return d + timedelta(weeks=interval_count)
    return add_calendar_months(d, _MONTHS_PER_UNIT[interval_unit] * interval_count)


def nth_occurrence(start_date: date, interval_unit: str, interval_count: int, n: int) -> date:
    """The n-th occurrence (n=0 is start_date itself) counted from start_date,
    always anchored to start_date's day-of-month rather than to the previous
    occurrence. This avoids permanent drift for month/quarter intervals: a
    line starting January 31 lands on February 28, but still lands on March
    31 (not March 28) since March is computed as start_date + 2 months, not
    as February's clamped date + 1 month."""
    if interval_unit == "week":
        return start_date + timedelta(weeks=interval_count * n)
    return add_calendar_months(start_date, _MONTHS_PER_UNIT[interval_unit] * interval_count * n)


def generate_occurrence_dates(
    start_date: date, interval_unit: str, interval_count: int, end_date: date | None
) -> list[date]:
    """Occurrence dates for a contract line: start_date, then every
    interval_unit/interval_count apart (real calendar weeks/months/quarters,
    anchored to start_date's day-of-month), up to end_date if set, else up to
    OPEN_ENDED_HORIZON_DAYS after start_date."""
    horizon = end_date or start_date + timedelta(days=OPEN_ENDED_HORIZON_DAYS)

    dates = []
    n = 0
    while True:
        current = nth_occurrence(start_date, interval_unit, interval_count, n)
        if current > horizon:
            break
        dates.append(current)
        n += 1
    return dates


def extend_occurrence_dates(
    start_date: date,
    interval_unit: str,
    interval_count: int,
    furthest_existing: date,
    new_horizon: date,
) -> list[date]:
    """Occurrence dates strictly after furthest_existing, continuing the same
    interval_unit/interval_count cadence anchored to start_date, up to and
    including new_horizon."""
    dates = []
    n = 1
    while True:
        current = nth_occurrence(start_date, interval_unit, interval_count, n)
        if current > new_horizon:
            break
        if current > furthest_existing:
            dates.append(current)
        n += 1
    return dates
