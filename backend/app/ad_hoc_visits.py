from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session, joinedload

from app.employee_schedule import resolve_employee_schedule
from app.models import Assignment, ContractLine, Employee
from app.qualification import required_skill_ids

FREE_SLOT_HORIZON_DAYS = 14

# Matches the solver's own start-time granularity (solver/app/domain.py,
# START_TIME_STEP_MINUTES) so a slot offered here is one the optimizer would
# also consider, without the two services sharing code.
FREE_SLOT_STEP_MINUTES = 15


@dataclass(frozen=True)
class FreeSlot:
    employee_id: int
    employee_name: str
    start: datetime
    end: datetime


def _minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


def _time_from_minutes(minutes: int) -> time:
    return time(hour=minutes // 60, minute=minutes % 60)


def _qualifying_employees(db: Session, contract_line: ContractLine) -> list[Employee]:
    region_id = contract_line.customer_location.region_id
    needed_skill_ids = required_skill_ids(contract_line)
    employees = (
        db.query(Employee)
        .filter(Employee.delete_flag.is_(False))
        .options(joinedload(Employee.regions), joinedload(Employee.skills))
        .all()
    )
    return [
        employee
        for employee in employees
        if region_id in {region.id for region in employee.regions}
        and needed_skill_ids.issubset({skill.id for skill in employee.skills})
    ]


def _busy_windows(db: Session, employee_id: int, target_date: date) -> list[tuple[int, int]]:
    """An employee's existing assignment windows (start/end minutes since
    midnight) for a date, keyed by the assignment's own planned day rather
    than the visit's requested_date, which may differ (e.g. a rescheduled
    past-due visit)."""
    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)
    assignments = (
        db.query(Assignment)
        .filter(
            Assignment.employee_id == employee_id,
            Assignment.planned_start >= day_start,
            Assignment.planned_start <= day_end,
        )
        .all()
    )
    return sorted(
        (_minutes_since_midnight(a.planned_start.time()), _minutes_since_midnight(a.planned_end.time()))
        for a in assignments
    )


def _find_gaps(
    work_start: int, work_end: int, busy_windows: list[tuple[int, int]], duration_minutes: int
) -> list[int]:
    """Start-minute offsets, stepped every FREE_SLOT_STEP_MINUTES, where a
    duration_minutes-long slot fits within [work_start, work_end] without
    overlapping any busy window."""
    starts = []
    cursor = work_start
    for busy_start, busy_end in busy_windows:
        while cursor + duration_minutes <= busy_start:
            starts.append(cursor)
            cursor += FREE_SLOT_STEP_MINUTES
        cursor = max(cursor, busy_end)
    while cursor + duration_minutes <= work_end:
        starts.append(cursor)
        cursor += FREE_SLOT_STEP_MINUTES
    return starts


def find_free_slots(db: Session, contract_line: ContractLine) -> list[FreeSlot]:
    """Every candidate free slot for a contract line over the next
    FREE_SLOT_HORIZON_DAYS days: an employee holding every skill the line's
    required products require, scoped to its region, with a resolved
    working-hours window and no conflicting existing assignment for that
    window."""
    employees = _qualifying_employees(db, contract_line)
    duration_minutes = contract_line.duration_minutes

    slots: list[FreeSlot] = []
    for offset in range(FREE_SLOT_HORIZON_DAYS):
        target_date = date.today() + timedelta(days=offset)
        for employee in employees:
            schedule = resolve_employee_schedule(db, employee.id, target_date)
            if schedule is None:
                continue
            work_start, work_end = schedule
            busy_windows = _busy_windows(db, employee.id, target_date)
            for start_minutes in _find_gaps(
                _minutes_since_midnight(work_start),
                _minutes_since_midnight(work_end),
                busy_windows,
                duration_minutes,
            ):
                start = datetime.combine(target_date, _time_from_minutes(start_minutes))
                slots.append(
                    FreeSlot(
                        employee_id=employee.id,
                        employee_name=employee.name,
                        start=start,
                        end=start + timedelta(minutes=duration_minutes),
                    )
                )
    return slots
