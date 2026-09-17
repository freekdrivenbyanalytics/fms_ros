from datetime import date, datetime, time, timedelta

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.employee_schedule import resolve_employee_schedule
from app.models import (
    Assignment,
    ContractLine,
    CustomerLocation,
    DrivingTime,
    Employee,
    Product,
    ServiceVisit,
)
from app.qualification import required_skill_ids

# Bounds solver problem size - see design.md ("days_ahead is capped at 14")
# in the add-optimize-run-parameters change.
MAX_DAYS_AHEAD = 14


def _minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


def effective_schedule_date(visit: ServiceVisit) -> date:
    """The date a schedule run may propose this visit on.

    A visit's own requested date, unless that date has already passed, in
    which case it's rescheduled to today rather than being stuck on a date
    that's already gone.
    """
    return max(visit.requested_date, date.today())


def _is_locked(assignment: Assignment) -> bool:
    """An assignment a schedule run must never touch: pinned, or already started."""
    return assignment.pinned or assignment.planned_start <= datetime.now()


def _employee_payload(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "employee_skill_ids": [s.id for s in employee.skills],
        "region_ids": [r.id for r in employee.regions],
        "latitude": employee.latitude,
        "longitude": employee.longitude,
    }


def _employee_day_schedule_payloads(
    db: Session, employees: list[Employee], dates: set[date]
) -> list[dict]:
    """One EmployeeDaySchedule entry per (employee, date) that resolves to an
    actual working-hours window; pairs with no schedule are omitted rather
    than sent with null hours, so the solver's if_not_exists constraint can
    tell an employee has no schedule that date."""
    schedules = []
    for employee in employees:
        for target_date in dates:
            resolved = resolve_employee_schedule(db, employee.id, target_date)
            if resolved is None:
                continue
            work_start, work_end = resolved
            schedules.append(
                {
                    "employee_id": employee.id,
                    "date": target_date.isoformat(),
                    "start_minutes": _minutes_since_midnight(work_start),
                    "end_minutes": _minutes_since_midnight(work_end),
                }
            )
    return schedules


def _visit_payload(visit: ServiceVisit) -> dict:
    location = visit.contract_line.customer_location
    return {
        "id": visit.id,
        "requested_date": effective_schedule_date(visit).isoformat(),
        "duration_minutes": visit.contract_line.duration_minutes,
        "required_skill_ids": list(required_skill_ids(visit.contract_line)),
        "region_id": location.region_id,
        "location_id": location.id,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "priority": visit.contract_line.priority,
        "days_until_due": (effective_schedule_date(visit) - date.today()).days,
    }


def _existing_assignment_payload(assignment: Assignment) -> dict:
    location = assignment.service_visit.contract_line.customer_location
    duration = int((assignment.planned_end - assignment.planned_start).total_seconds() // 60)
    start_minutes = _minutes_since_midnight(assignment.planned_start.time())
    return {
        "id": str(assignment.service_visit_id),
        "employee_id": assignment.employee_id,
        "requested_date": assignment.service_visit.requested_date.isoformat(),
        "start_minutes": start_minutes,
        "end_minutes": start_minutes + duration,
        "location_id": location.id,
        "latitude": location.latitude,
        "longitude": location.longitude,
    }


def _is_ready_to_schedule(visit: ServiceVisit) -> bool:
    """A visit the optimizer can consider: its location has resolved
    coordinates and an assigned region. Neither is guaranteed for a
    Tripletex-synced location until geocoding/region-assignment happens."""
    location = visit.contract_line.customer_location
    return (
        location.latitude is not None
        and location.longitude is not None
        and location.region_id is not None
    )


def _is_within_scheduling_window(visit: ServiceVisit, days_ahead: int) -> bool:
    """A schedule run only ever proposes visits within days_ahead days of
    today (today itself counting as day 0), capped at MAX_DAYS_AHEAD to keep
    the solver's problem size to what's actually actionable."""
    today = date.today()
    window = {today + timedelta(days=d) for d in range(min(days_ahead, MAX_DAYS_AHEAD))}
    return effective_schedule_date(visit) in window


def _driving_time_payloads(db: Session, region_ids: set[int]) -> list[dict]:
    if not region_ids:
        return []
    rows = db.query(DrivingTime).filter(DrivingTime.region_id.in_(region_ids)).all()
    return [
        {
            "origin_kind": row.origin_kind.value,
            "origin_id": row.origin_id,
            "destination_kind": row.destination_kind.value,
            "destination_id": row.destination_id,
            "duration_minutes": row.duration_minutes,
        }
        for row in rows
    ]


def build_optimize_payload(
    db: Session, days_ahead: int = 2, time_limit_seconds: int | None = None
) -> tuple[dict, list[int]]:
    """Build the solver request payload.

    Returns (payload, excluded_visit_ids): payload is what's sent to the
    solver; excluded_visit_ids are candidate visits the solver never even
    sees (no resolved location), which the caller should still report as
    unscheduled since the solver's own response won't mention them.
    """
    employees = (
        db.query(Employee)
        .filter(Employee.delete_flag.is_(False))
        .options(joinedload(Employee.regions), joinedload(Employee.skills))
        .order_by(Employee.id)
        .all()
    )
    all_visits = (
        db.query(ServiceVisit)
        .options(
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.skills),
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
            joinedload(ServiceVisit.assignment),
        )
        .order_by(ServiceVisit.id)
        .all()
    )

    # A visit is schedulable unless it has a locked assignment (pinned, or
    # already started); a not-yet-started unpinned assignment moves it from
    # "existing fact" to "candidate" rather than appearing in both.
    schedulable_visits = [v for v in all_visits if v.assignment is None or not _is_locked(v.assignment)]
    locked_assignments = [v.assignment for v in all_visits if v.assignment is not None and _is_locked(v.assignment)]

    ready_visits = [
        v
        for v in schedulable_visits
        if _is_ready_to_schedule(v) and _is_within_scheduling_window(v, days_ahead)
    ]
    excluded_visit_ids = [
        v.id
        for v in schedulable_visits
        if not (_is_ready_to_schedule(v) and _is_within_scheduling_window(v, days_ahead))
    ]

    candidate_dates = {effective_schedule_date(v) for v in ready_visits}

    region_ids = {v.contract_line.customer_location.region_id for v in ready_visits}
    region_ids.update(r.id for e in employees for r in e.regions)

    payload = {
        "employees": [_employee_payload(e) for e in employees],
        "employee_day_schedules": _employee_day_schedule_payloads(db, employees, candidate_dates),
        "visits": [_visit_payload(v) for v in ready_visits],
        "existing_assignments": [_existing_assignment_payload(a) for a in locked_assignments],
        "driving_times": _driving_time_payloads(db, region_ids),
        "time_limit_seconds": time_limit_seconds or settings.solver_time_limit_seconds,
    }
    return payload, excluded_visit_ids


def request_proposal(payload: dict) -> dict:
    timeout = settings.solver_time_limit_seconds + 10
    response = httpx.post(f"{settings.solver_base_url}/optimize", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
