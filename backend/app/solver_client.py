from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
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
from app.solver_partitioning import group_regions_by_shared_employees

# Bounds solver problem size - see design.md ("days_ahead is capped at 14")
# in the add-optimize-run-parameters change.
MAX_DAYS_AHEAD = 14


def _minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


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


def apply_plan_from_floor(
    start_minutes: int, end_minutes: int, is_today: bool, plan_from_minutes: int | None
) -> tuple[int, int] | None:
    """Clamp a resolved (start_minutes, end_minutes) working-hours window
    against a plan-from-time floor, for today only.

    Returns the (possibly unchanged) window, or None when the floor
    consumes the entire remaining window - the caller should then omit that
    day's entry, same as when there's no resolved schedule at all."""
    if plan_from_minutes is None or not is_today:
        return start_minutes, end_minutes
    start_minutes = max(start_minutes, plan_from_minutes)
    if start_minutes >= end_minutes:
        return None
    return start_minutes, end_minutes


def _employee_day_schedule_payloads(
    db: Session,
    employees: list[Employee],
    dates: set[date],
    plan_from_time: str | None = None,
) -> list[dict]:
    """One EmployeeDaySchedule entry per (employee, date) that resolves to an
    actual working-hours window; pairs with no schedule are omitted rather
    than sent with null hours, so the solver's if_not_exists constraint can
    tell an employee has no schedule that date.

    plan_from_time, when given, floors today's start_minutes to no earlier
    than that time (never earlier than the employee's own resolved start);
    every other date is unaffected. See apply_plan_from_floor."""
    plan_from_minutes = (
        _minutes_since_midnight(_parse_hhmm(plan_from_time)) if plan_from_time else None
    )
    today = date.today()
    schedules = []
    for employee in employees:
        for target_date in dates:
            resolved = resolve_employee_schedule(db, employee.id, target_date)
            if resolved is None:
                continue
            work_start, work_end = resolved
            clamped = apply_plan_from_floor(
                _minutes_since_midnight(work_start),
                _minutes_since_midnight(work_end),
                target_date == today,
                plan_from_minutes,
            )
            if clamped is None:
                continue
            start_minutes, end_minutes = clamped
            schedules.append(
                {
                    "employee_id": employee.id,
                    "date": target_date.isoformat(),
                    "start_minutes": start_minutes,
                    "end_minutes": end_minutes,
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


@dataclass
class _RunData:
    employees: list[Employee]
    ready_visits: list[ServiceVisit]
    locked_assignments: list[Assignment]
    excluded_visit_ids: list[int]
    candidate_dates: set[date]
    all_region_ids: set[int]


def _load_run_data(db: Session, days_ahead: int) -> _RunData:
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

    return _RunData(
        employees=employees,
        ready_visits=ready_visits,
        locked_assignments=locked_assignments,
        excluded_visit_ids=excluded_visit_ids,
        candidate_dates=candidate_dates,
        all_region_ids=region_ids,
    )


def _assemble_payload(
    db: Session,
    employees: list[Employee],
    visits: list[ServiceVisit],
    locked_assignments: list[Assignment],
    candidate_dates: set[date],
    region_ids: set[int],
    time_limit_seconds: int | None,
    plan_from_time: str | None = None,
) -> dict:
    return {
        "employees": [_employee_payload(e) for e in employees],
        "employee_day_schedules": _employee_day_schedule_payloads(
            db, employees, candidate_dates, plan_from_time
        ),
        "visits": [_visit_payload(v) for v in visits],
        "existing_assignments": [_existing_assignment_payload(a) for a in locked_assignments],
        "driving_times": _driving_time_payloads(db, region_ids),
        "time_limit_seconds": time_limit_seconds or settings.solver_time_limit_seconds,
    }


def build_optimize_payload(
    db: Session,
    days_ahead: int = 2,
    time_limit_seconds: int | None = None,
    plan_from_time: str | None = None,
) -> tuple[dict, list[int]]:
    """Build the solver request payload.

    Returns (payload, excluded_visit_ids): payload is what's sent to the
    solver; excluded_visit_ids are candidate visits the solver never even
    sees (no resolved location), which the caller should still report as
    unscheduled since the solver's own response won't mention them.
    """
    data = _load_run_data(db, days_ahead)
    payload = _assemble_payload(
        db,
        data.employees,
        data.ready_visits,
        data.locked_assignments,
        data.candidate_dates,
        data.all_region_ids,
        time_limit_seconds,
        plan_from_time,
    )
    return payload, data.excluded_visit_ids


def _group_subset(
    data: _RunData, group_region_ids: set[int]
) -> tuple[list[Employee], list[ServiceVisit], list[Assignment], set[date], set[int]]:
    group_employees = [e for e in data.employees if {r.id for r in e.regions} & group_region_ids]
    group_employee_ids = {e.id for e in group_employees}
    group_visits = [
        v
        for v in data.ready_visits
        if v.contract_line.customer_location.region_id in group_region_ids
    ]
    group_locked = [a for a in data.locked_assignments if a.employee_id in group_employee_ids]
    group_dates = {effective_schedule_date(v) for v in group_visits}
    return group_employees, group_visits, group_locked, group_dates, group_region_ids


def build_parallel_group_payloads(
    db: Session,
    days_ahead: int = 2,
    time_limit_seconds: int | None = None,
    plan_from_time: str | None = None,
) -> tuple[list[dict] | None, list[int]]:
    """Build one payload per employee-disjoint region group, for `parallel`
    execution mode.

    Each group's payload is a real subset of the full run's
    employees/visits/driving-times/existing-assignments: only rows
    belonging to that group's regions/employees, built with the same
    per-item payload builders `build_optimize_payload` uses.

    Returns (group_payloads, excluded_visit_ids). group_payloads is None
    when the run's ready-to-schedule visits' regions form a single connected
    group (including zero or one region) - the caller should fall back to
    `build_optimize_payload`'s ordinary single-call path in that case, since
    there is nothing to usefully split.
    """
    data = _load_run_data(db, days_ahead)
    region_ids_with_visits = {v.contract_line.customer_location.region_id for v in data.ready_visits}
    groups = group_regions_by_shared_employees(data.employees, region_ids_with_visits)
    if len(groups) < 2:
        return None, data.excluded_visit_ids
    group_payloads = [
        _assemble_payload(
            db, *_group_subset(data, group_region_ids), time_limit_seconds, plan_from_time
        )
        for group_region_ids in groups
    ]
    return group_payloads, data.excluded_visit_ids


def request_proposal(payload: dict) -> dict:
    timeout = settings.solver_time_limit_seconds + 10
    response = httpx.post(f"{settings.solver_base_url}/optimize", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def request_parallel_proposals(payloads: list[dict]) -> dict:
    """Dispatch one solver call per group concurrently and merge the results
    into one response, in the same shape `request_proposal` returns.

    Only called with 2+ payloads (see `build_parallel_group_payloads`); a
    single group is handled by `request_proposal` directly instead. A
    failure in any one group's call propagates (matching a single-call
    failure) rather than returning a partial merge.
    """
    with ThreadPoolExecutor(max_workers=len(payloads)) as pool:
        results = list(pool.map(request_proposal, payloads))
    return {
        "scheduled": [item for result in results for item in result["scheduled"]],
        "unscheduled_visit_ids": [
            visit_id for result in results for visit_id in result["unscheduled_visit_ids"]
        ],
    }
