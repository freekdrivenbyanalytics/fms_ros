from datetime import date

import pytest
from app.constraints import define_constraints, unscheduled_visit
from app.domain import Schedule, VisitAssignment
from app.schemas import (
    DrivingTimeIn,
    EmployeeDayScheduleIn,
    EmployeeIn,
    OptimizeRequest,
    VisitIn,
)
from app.solve import solve_schedule
from timefold.solver.test import ConstraintVerifier

DAY = date(2026, 1, 5)
URGENCY_CAP = 14
URGENCY_UPPER_BOUND = URGENCY_CAP + 1


def _expected_weight(priority: int, days_until_due: int, total_visit_count: int) -> int:
    """Mirrors constraints.py's _unscheduled_priority_weight, independently,
    so these tests would catch a regression in the formula itself."""
    urgency = URGENCY_CAP - days_until_due
    if priority >= 3:
        return urgency
    tier_2 = total_visit_count * URGENCY_UPPER_BOUND + 1
    if priority == 2:
        return tier_2 + urgency
    tier_1 = total_visit_count * (tier_2 + URGENCY_UPPER_BOUND) + 1
    return tier_1 + urgency


def _unassigned_visit(
    visit_id: int, priority: int, days_until_due: int, total_visit_count: int
) -> VisitAssignment:
    return VisitAssignment(
        id=visit_id,
        requested_date=DAY,
        duration_minutes=60,
        required_skill_ids=frozenset(),
        region_id=1,
        location_id=100 + visit_id,
        latitude=52.0,
        longitude=5.0,
        priority=priority,
        days_until_due=days_until_due,
        total_visit_count=total_visit_count,
    )


@pytest.fixture(scope="module")
def verifier() -> ConstraintVerifier:
    return ConstraintVerifier.build(define_constraints, Schedule, VisitAssignment)


def test_higher_priority_unscheduled_visit_penalizes_more(verifier: ConstraintVerifier) -> None:
    high_priority = _unassigned_visit(1, priority=1, days_until_due=0, total_visit_count=2)
    low_priority = _unassigned_visit(2, priority=3, days_until_due=0, total_visit_count=2)

    verifier.verify_that(unscheduled_visit).given(high_priority).penalizes_by(
        _expected_weight(1, 0, 2)
    )
    verifier.verify_that(unscheduled_visit).given(low_priority).penalizes_by(
        _expected_weight(3, 0, 2)
    )
    assert _expected_weight(1, 0, 2) > _expected_weight(3, 0, 2)


def test_more_urgent_same_priority_visit_penalizes_more(verifier: ConstraintVerifier) -> None:
    urgent = _unassigned_visit(1, priority=2, days_until_due=0, total_visit_count=2)
    distant = _unassigned_visit(2, priority=2, days_until_due=10, total_visit_count=2)

    verifier.verify_that(unscheduled_visit).given(urgent).penalizes_by(
        _expected_weight(2, 0, 2)
    )
    verifier.verify_that(unscheduled_visit).given(distant).penalizes_by(
        _expected_weight(2, 10, 2)
    )
    assert _expected_weight(2, 0, 2) > _expected_weight(2, 10, 2)


def test_a_single_priority_1_unscheduled_visit_outweighs_many_priority_3_visits(
    verifier: ConstraintVerifier,
) -> None:
    # N (total_visit_count) must be a true upper bound on how many visits
    # could ever be unscheduled together - here, 201 visits total, so the
    # nested scale must survive summing the other 200 all at priority 3.
    n = 201
    high = _unassigned_visit(1, priority=1, days_until_due=0, total_visit_count=n)
    many_low = [
        _unassigned_visit(i, priority=3, days_until_due=0, total_visit_count=n)
        for i in range(2, n + 1)
    ]

    high_penalty = _expected_weight(1, 0, n)
    low_total_penalty = sum(_expected_weight(3, 0, n) for _ in many_low)
    assert high_penalty > low_total_penalty

    verifier.verify_that(unscheduled_visit).given(high).penalizes_by(high_penalty)
    verifier.verify_that(unscheduled_visit).given(*many_low).penalizes_by(low_total_penalty)


def test_priority_does_not_override_scheduling_more_visits_than_fewer() -> None:
    # A priority-1 visit and a priority-3 visit compete for the same
    # employee/time slot (identical location and a working-hours window too
    # short to fit both). The solver should still schedule one of them
    # rather than leaving both unscheduled to "protect" the higher-priority
    # visit's flexibility - scheduling more visits always beats scheduling
    # fewer, regardless of priority.
    request = OptimizeRequest(
        employees=[
            EmployeeIn(id=1, employee_skill_ids=[], region_ids=[1], latitude=52.0, longitude=5.0)
        ],
        employee_day_schedules=[
            EmployeeDayScheduleIn(
                employee_id=1, date="2026-01-05", start_minutes=480, end_minutes=540
            )
        ],
        visits=[
            VisitIn(
                id=1,
                requested_date="2026-01-05",
                duration_minutes=60,
                required_skill_ids=[],
                region_id=1,
                location_id=100,
                latitude=52.0,
                longitude=5.0,
                priority=1,
                days_until_due=0,
            ),
            VisitIn(
                id=2,
                requested_date="2026-01-05",
                duration_minutes=60,
                required_skill_ids=[],
                region_id=1,
                location_id=100,
                latitude=52.0,
                longitude=5.0,
                priority=3,
                days_until_due=0,
            ),
        ],
        driving_times=[
            DrivingTimeIn(
                origin_kind="employee",
                origin_id=1,
                destination_kind="customer_location",
                destination_id=100,
                duration_minutes=0,
            )
        ],
        time_limit_seconds=5,
    )

    response = solve_schedule(request)

    assert len(response.scheduled) == 1
    assert len(response.unscheduled_visit_ids) == 1
