from datetime import time

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import Assignment, Contract, CustomerLocation, Employee, ServiceVisit


def _minutes_since_midnight(t: time) -> int:
    return t.hour * 60 + t.minute


def _employee_payload(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "work_start_minutes": _minutes_since_midnight(employee.work_start),
        "work_end_minutes": _minutes_since_midnight(employee.work_end),
        "skill_ids": [s.id for s in employee.skills],
        "region_ids": [r.id for r in employee.regions],
        "latitude": employee.latitude,
        "longitude": employee.longitude,
    }


def _visit_payload(visit: ServiceVisit) -> dict:
    location = visit.contract.customer_location
    return {
        "id": visit.id,
        "requested_date": visit.requested_date.isoformat(),
        "duration_minutes": visit.contract.duration_minutes,
        "required_skill_ids": [s.id for s in visit.contract.required_skills],
        "region_id": location.region_id,
        "latitude": location.latitude,
        "longitude": location.longitude,
    }


def _existing_assignment_payload(assignment: Assignment) -> dict:
    location = assignment.service_visit.contract.customer_location
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


def build_optimize_payload(db: Session) -> dict:
    employees = (
        db.query(Employee)
        .options(joinedload(Employee.regions), joinedload(Employee.skills))
        .order_by(Employee.id)
        .all()
    )
    all_visits = (
        db.query(ServiceVisit)
        .options(
            joinedload(ServiceVisit.contract).joinedload(Contract.required_skills),
            joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
            .joinedload(CustomerLocation.region),
            joinedload(ServiceVisit.assignment),
        )
        .order_by(ServiceVisit.id)
        .all()
    )

    # A visit is schedulable unless it has a pinned assignment; an unpinned
    # assignment moves it from "existing fact" to "candidate" rather than
    # appearing in both.
    schedulable_visits = [v for v in all_visits if v.assignment is None or not v.assignment.pinned]
    pinned_assignments = [v.assignment for v in all_visits if v.assignment is not None and v.assignment.pinned]

    return {
        "employees": [_employee_payload(e) for e in employees],
        "visits": [_visit_payload(v) for v in schedulable_visits],
        "existing_assignments": [_existing_assignment_payload(a) for a in pinned_assignments],
        "time_limit_seconds": settings.solver_time_limit_seconds,
    }


def request_proposal(payload: dict) -> dict:
    timeout = settings.solver_time_limit_seconds + 10
    response = httpx.post(f"{settings.solver_base_url}/optimize", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
