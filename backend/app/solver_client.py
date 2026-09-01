from datetime import date, datetime, time

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.employee_schedule import resolve_employee_schedule
from app.models import Assignment, ContractLine, CustomerLocation, Employee, ServiceVisit


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
        "skill_ids": [s.id for s in employee.skills],
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
        "required_skill_ids": [s.id for s in visit.contract_line.required_skills],
        "region_id": location.region_id,
        "latitude": location.latitude,
        "longitude": location.longitude,
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


def build_optimize_payload(db: Session) -> tuple[dict, list[int]]:
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
            joinedload(ServiceVisit.contract_line).joinedload(ContractLine.required_skills),
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

    ready_visits = [v for v in schedulable_visits if _is_ready_to_schedule(v)]
    excluded_visit_ids = [v.id for v in schedulable_visits if not _is_ready_to_schedule(v)]

    candidate_dates = {effective_schedule_date(v) for v in ready_visits}

    payload = {
        "employees": [_employee_payload(e) for e in employees],
        "employee_day_schedules": _employee_day_schedule_payloads(db, employees, candidate_dates),
        "visits": [_visit_payload(v) for v in ready_visits],
        "existing_assignments": [_existing_assignment_payload(a) for a in locked_assignments],
        "time_limit_seconds": settings.solver_time_limit_seconds,
    }
    return payload, excluded_visit_ids


def request_proposal(payload: dict) -> dict:
    timeout = settings.solver_time_limit_seconds + 10
    response = httpx.post(f"{settings.solver_base_url}/optimize", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
