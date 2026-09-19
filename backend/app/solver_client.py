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


def _visit_payload(
    visit: ServiceVisit,
    previous_occurrence: tuple[int | None, date | None, int | None],
) -> dict:
    """previous_occurrence is (previous_visit_id, previous_actual_date,
    interval_days) - see _compute_previous_occurrences."""
    location = visit.contract_line.customer_location
    previous_visit_id, previous_actual_date, interval_days = previous_occurrence
    return {
        "id": visit.id,
        # The true nominal (contract-cadence) date - no longer floored to
        # today. It's now only the preference anchor the solver's `date`
        # choice is scored against, not the date it must land on.
        "requested_date": visit.requested_date.isoformat(),
        "duration_minutes": visit.contract_line.duration_minutes,
        "required_skill_ids": list(required_skill_ids(visit.contract_line)),
        "region_id": location.region_id,
        "location_id": location.id,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "priority": visit.contract_line.priority,
        "days_until_due": (effective_schedule_date(visit) - date.today()).days,
        "interval_days": interval_days,
        "previous_visit_id": previous_visit_id,
        "previous_actual_date": previous_actual_date.isoformat() if previous_actual_date else None,
    }


def _existing_assignment_payload(assignment: Assignment) -> dict:
    location = assignment.service_visit.contract_line.customer_location
    duration = int((assignment.planned_end - assignment.planned_start).total_seconds() // 60)
    start_minutes = _minutes_since_midnight(assignment.planned_start.time())
    return {
        "id": str(assignment.service_visit_id),
        "employee_id": assignment.employee_id,
        # The date this assignment actually occupies - not the visit's
        # nominal requested_date, which can differ once rescheduled.
        "date": assignment.planned_start.date().isoformat(),
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


def _window_dates(days_ahead: int) -> set[date]:
    """Every date in the run's scheduling window - today through today +
    min(days_ahead, MAX_DAYS_AHEAD) - 1. This is both the solver's `date`
    planning variable's value range and the set of dates every employee's
    working-hours schedule must be sent for, since a visit may now be
    proposed on any date in the window, not only the dates visits happen to
    nominally fall on."""
    today = date.today()
    return {today + timedelta(days=d) for d in range(min(days_ahead, MAX_DAYS_AHEAD))}


def _is_within_scheduling_window(visit: ServiceVisit, days_ahead: int) -> bool:
    """A schedule run only ever proposes visits within days_ahead days of
    today (today itself counting as day 0), capped at MAX_DAYS_AHEAD to keep
    the solver's problem size to what's actually actionable."""
    return effective_schedule_date(visit) in _window_dates(days_ahead)


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


# (previous_visit_id, previous_actual_date, interval_days) - see
# _compute_previous_occurrences.
_PreviousOccurrence = tuple[int | None, date | None, int | None]
_NO_PREVIOUS_OCCURRENCE: _PreviousOccurrence = (None, None, None)


def _compute_previous_occurrences(
    all_visits: list[ServiceVisit],
) -> dict[int, _PreviousOccurrence]:
    """For every visit, find its contract line's immediately preceding
    occurrence (by requested_date) among all_visits - already loaded by
    _load_run_data, no new query needed - and resolve it to exactly one of:

    - previous_visit_id: the preceding occurrence, when it's itself
      schedulable this run (no locked assignment) - its own `date` is being
      jointly decided too, so the solver compares chosen dates directly.
    - previous_actual_date: the preceding occurrence's actual date, when it
      has a locked assignment instead (pinned, already started, or
      otherwise fixed) - a plain fact, not a decision.
    - neither, when there is no preceding occurrence (the contract line's
      first visit) or the preceding occurrence couldn't be resolved (e.g.
      not ready to schedule) - the interval preference simply doesn't apply.
    """
    by_contract_line: dict[int, list[ServiceVisit]] = {}
    for v in all_visits:
        by_contract_line.setdefault(v.contract_line_id, []).append(v)

    result: dict[int, _PreviousOccurrence] = {}
    for visits in by_contract_line.values():
        ordered = sorted(visits, key=lambda v: v.requested_date)
        for i, visit in enumerate(ordered):
            if i == 0:
                result[visit.id] = _NO_PREVIOUS_OCCURRENCE
                continue
            previous = ordered[i - 1]
            interval_days = (visit.requested_date - previous.requested_date).days
            if previous.assignment is not None and _is_locked(previous.assignment):
                result[visit.id] = (None, previous.assignment.planned_start.date(), interval_days)
            else:
                result[visit.id] = (previous.id, None, interval_days)
    return result


@dataclass
class _RunData:
    employees: list[Employee]
    ready_visits: list[ServiceVisit]
    locked_assignments: list[Assignment]
    excluded_visit_ids: list[int]
    candidate_dates: set[date]
    all_region_ids: set[int]
    previous_occurrence_by_visit_id: dict[int, _PreviousOccurrence]


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

    # The full scheduling window, not just the dates visits happen to
    # nominally fall on - a visit may now be proposed on any date in it.
    candidate_dates = _window_dates(days_ahead)

    region_ids = {v.contract_line.customer_location.region_id for v in ready_visits}
    region_ids.update(r.id for e in employees for r in e.regions)

    previous_occurrence_by_visit_id = _compute_previous_occurrences(all_visits)

    return _RunData(
        employees=employees,
        ready_visits=ready_visits,
        locked_assignments=locked_assignments,
        excluded_visit_ids=excluded_visit_ids,
        candidate_dates=candidate_dates,
        all_region_ids=region_ids,
        previous_occurrence_by_visit_id=previous_occurrence_by_visit_id,
    )


def _default_time_limit_seconds(window_days: int) -> int:
    """The solver time budget to use when the caller doesn't specify one,
    scaled with the scheduling window size.

    A flat `settings.solver_time_limit_seconds` (30s) was tuned for the old
    single-day solve. The multi-day `date` planning variable multiplies
    each visit's search space by the window size, and testing against a
    realistic dataset (~150 visits, 3 employees) showed solve quality
    visibly degrading at a flat 30s as days_ahead grows - fewer visits
    scheduled than the single-day baseline, and no spread to later days at
    all. Scaling the default recovers some of that quality; it does not
    fully resolve it at this data volume - see design.md's Risks and the
    follow-up change exploring solver tuning and mandatory region-splitting
    at larger problem sizes. Capped at 90s to stay within a practical
    bound for a synchronous request.
    """
    return min(settings.solver_time_limit_seconds + 10 * (window_days - 1), 90)


def _assemble_payload(
    db: Session,
    employees: list[Employee],
    visits: list[ServiceVisit],
    locked_assignments: list[Assignment],
    candidate_dates: set[date],
    region_ids: set[int],
    time_limit_seconds: int | None,
    previous_occurrence_by_visit_id: dict[int, _PreviousOccurrence],
    plan_from_time: str | None = None,
) -> dict:
    return {
        "employees": [_employee_payload(e) for e in employees],
        "employee_day_schedules": _employee_day_schedule_payloads(
            db, employees, candidate_dates, plan_from_time
        ),
        "visits": [
            _visit_payload(
                v, previous_occurrence_by_visit_id.get(v.id, _NO_PREVIOUS_OCCURRENCE)
            )
            for v in visits
        ],
        "existing_assignments": [_existing_assignment_payload(a) for a in locked_assignments],
        "driving_times": _driving_time_payloads(db, region_ids),
        "candidate_dates": sorted(d.isoformat() for d in candidate_dates),
        "time_limit_seconds": time_limit_seconds or _default_time_limit_seconds(len(candidate_dates)),
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
        data.previous_occurrence_by_visit_id,
        plan_from_time,
    )
    return payload, data.excluded_visit_ids


def _group_subset(
    data: _RunData, group_region_ids: set[int]
) -> tuple[list[Employee], list[ServiceVisit], list[Assignment], set[date], set[int]]:
    """A group's own employees/visits/locked-assignments, but sharing the
    full run's candidate_dates - the region split is orthogonal to date, so
    every group needs the same full-window schedule/date coverage as the
    single-mode path."""
    group_employees = [e for e in data.employees if {r.id for r in e.regions} & group_region_ids]
    group_employee_ids = {e.id for e in group_employees}
    group_visits = [
        v
        for v in data.ready_visits
        if v.contract_line.customer_location.region_id in group_region_ids
    ]
    group_locked = [a for a in data.locked_assignments if a.employee_id in group_employee_ids]
    return group_employees, group_visits, group_locked, data.candidate_dates, group_region_ids


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
            db,
            *_group_subset(data, group_region_ids),
            time_limit_seconds,
            data.previous_occurrence_by_visit_id,
            plan_from_time,
        )
        for group_region_ids in groups
    ]
    return group_payloads, data.excluded_visit_ids


def request_proposal(payload: dict) -> dict:
    # Must track the payload's own time_limit_seconds, not a flat default -
    # _default_time_limit_seconds scales it with the window size, and a
    # fixed timeout here would cut the request off before the solver's own
    # time limit elapses.
    timeout = payload["time_limit_seconds"] + 10
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
