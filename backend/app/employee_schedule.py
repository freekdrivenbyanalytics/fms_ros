from datetime import date, time

from sqlalchemy.orm import Session

from app.models import DayType, EmployeeScheduleDayOverride, EmployeeScheduleTemplate

_INFINITY = date.max


def covering_template(
    db: Session, employee_id: int, target_date: date
) -> EmployeeScheduleTemplate | None:
    return (
        db.query(EmployeeScheduleTemplate)
        .filter(
            EmployeeScheduleTemplate.employee_id == employee_id,
            EmployeeScheduleTemplate.delete_flag.is_(False),
            EmployeeScheduleTemplate.start_date <= target_date,
            (EmployeeScheduleTemplate.end_date.is_(None))
            | (EmployeeScheduleTemplate.end_date >= target_date),
        )
        .first()
    )


def resolve_employee_schedule(
    db: Session, employee_id: int, target_date: date
) -> tuple[time, time] | None:
    """An employee's effective working-hours window for a date: override,
    else covering template, else no schedule that date. Never reads
    overtime_minutes — overtime is recorded but not solver-visible."""
    override = (
        db.query(EmployeeScheduleDayOverride)
        .filter(
            EmployeeScheduleDayOverride.employee_id == employee_id,
            EmployeeScheduleDayOverride.date == target_date,
            EmployeeScheduleDayOverride.delete_flag.is_(False),
        )
        .first()
    )

    if override is not None:
        if override.day_type in (DayType.HOLIDAY, DayType.SICK):
            return None
        if override.work_start is not None and override.work_end is not None:
            return (override.work_start, override.work_end)

    template = covering_template(db, employee_id, target_date)
    if template is not None:
        return (template.work_start, template.work_end)
    return None


def templates_overlap(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date | None,
    exclude_id: int | None = None,
) -> bool:
    """Whether a template with this date range would overlap another
    non-deleted template already persisted for the same employee."""
    end = end_date or _INFINITY
    query = db.query(EmployeeScheduleTemplate).filter(
        EmployeeScheduleTemplate.employee_id == employee_id,
        EmployeeScheduleTemplate.delete_flag.is_(False),
        EmployeeScheduleTemplate.start_date <= end,
        (EmployeeScheduleTemplate.end_date.is_(None))
        | (EmployeeScheduleTemplate.end_date >= start_date),
    )
    if exclude_id is not None:
        query = query.filter(EmployeeScheduleTemplate.id != exclude_id)
    return query.first() is not None


def override_exists_for_date(
    db: Session, employee_id: int, target_date: date, exclude_id: int | None = None
) -> bool:
    query = db.query(EmployeeScheduleDayOverride).filter(
        EmployeeScheduleDayOverride.employee_id == employee_id,
        EmployeeScheduleDayOverride.date == target_date,
        EmployeeScheduleDayOverride.delete_flag.is_(False),
    )
    if exclude_id is not None:
        query = query.filter(EmployeeScheduleDayOverride.id != exclude_id)
    return query.first() is not None


def _hours_between(work_start: time, work_end: time) -> float:
    start_minutes = work_start.hour * 60 + work_start.minute
    end_minutes = work_end.hour * 60 + work_end.minute
    return (end_minutes - start_minutes) / 60


def hours_exceed_cap(work_start: time, work_end: time, max_hours_per_day: float) -> bool:
    return _hours_between(work_start, work_end) > max_hours_per_day


def effective_max_hours_per_day(
    override_max_hours_per_day: float | None, template: EmployeeScheduleTemplate | None
) -> float | None:
    if override_max_hours_per_day is not None:
        return override_max_hours_per_day
    return template.max_hours_per_day if template is not None else None
