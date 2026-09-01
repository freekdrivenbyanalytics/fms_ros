from datetime import date, timedelta

OPEN_ENDED_HORIZON_DAYS = 365


def generate_occurrence_dates(
    start_date: date, interval_days: int, end_date: date | None
) -> list[date]:
    """Occurrence dates for a contract line: start_date, then every
    interval_days apart, up to end_date if set, else up to
    OPEN_ENDED_HORIZON_DAYS after start_date. A non-positive interval_days
    would otherwise loop forever, so it yields a single occurrence instead."""
    horizon = end_date or start_date + timedelta(days=OPEN_ENDED_HORIZON_DAYS)
    if interval_days <= 0:
        return [start_date] if start_date <= horizon else []

    dates = []
    current = start_date
    while current <= horizon:
        dates.append(current)
        current += timedelta(days=interval_days)
    return dates
