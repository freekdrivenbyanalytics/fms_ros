from datetime import date

import pytest
from app.constraints import (
    define_constraints,
    driving_time_gap_before_first_visit,
    driving_time_gap_before_first_visit_fallback,
    driving_time_gap_between_proposed_visits,
    driving_time_gap_between_proposed_visits_fallback,
    driving_time_gap_to_existing_assignment,
    driving_time_gap_to_existing_assignment_fallback,
)
from app.domain import (
    DrivingTimeFact,
    Employee,
    EmployeeDaySchedule,
    ExistingAssignmentFact,
    Schedule,
    VisitAssignment,
)
from timefold.solver.test import ConstraintVerifier

DAY = date(2026, 1, 5)

EMPLOYEE = Employee(
    id=1,
    product_ids=frozenset(),
    region_ids=frozenset({1}),
    latitude=52.0,
    longitude=5.0,
)


def _visit(visit_id: int, start_minutes: int, duration_minutes: int, location_id: int) -> VisitAssignment:
    return VisitAssignment(
        id=visit_id,
        requested_date=DAY,
        duration_minutes=duration_minutes,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=location_id,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=start_minutes,
    )


@pytest.fixture(scope="module")
def verifier() -> ConstraintVerifier:
    return ConstraintVerifier.build(define_constraints, Schedule, VisitAssignment)


def test_gap_smaller_than_driving_time_is_penalized(verifier: ConstraintVerifier) -> None:
    # Visit 1 ends at 10:00 (600 min), visit 2 starts at 10:10 (610 min):
    # only a 10-minute gap for a driving time of 20 minutes.
    earlier = _visit(1, start_minutes=540, duration_minutes=60, location_id=100)
    later = _visit(2, start_minutes=610, duration_minutes=60, location_id=200)
    driving_time = DrivingTimeFact(
        origin_kind="customer_location",
        origin_id=100,
        destination_kind="customer_location",
        destination_id=200,
        duration_minutes=20,
    )
    verifier.verify_that(driving_time_gap_between_proposed_visits).given(
        earlier, later, driving_time
    ).penalizes(1)


def test_gap_equal_to_driving_time_is_not_penalized(verifier: ConstraintVerifier) -> None:
    earlier = _visit(1, start_minutes=540, duration_minutes=60, location_id=100)
    later = _visit(2, start_minutes=620, duration_minutes=60, location_id=200)
    driving_time = DrivingTimeFact(
        origin_kind="customer_location",
        origin_id=100,
        destination_kind="customer_location",
        destination_id=200,
        duration_minutes=20,
    )
    verifier.verify_that(driving_time_gap_between_proposed_visits).given(
        earlier, later, driving_time
    ).penalizes(0)


def test_gap_smaller_than_fallback_estimate_is_penalized(verifier: ConstraintVerifier) -> None:
    earlier = VisitAssignment(
        id=1,
        requested_date=DAY,
        duration_minutes=60,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=100,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=540,
    )
    # ~52.1,5.1 is roughly 10km from 52.0,5.0 - at the assumed 40 km/h that's
    # about 15 minutes, comfortably more than the 1-minute gap below.
    later = VisitAssignment(
        id=2,
        requested_date=DAY,
        duration_minutes=60,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=200,
        latitude=52.1,
        longitude=5.1,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=601,
    )
    verifier.verify_that(driving_time_gap_between_proposed_visits_fallback).given(
        earlier, later
    ).penalizes(1)


def test_gap_at_least_fallback_estimate_is_not_penalized(verifier: ConstraintVerifier) -> None:
    earlier = VisitAssignment(
        id=1,
        requested_date=DAY,
        duration_minutes=60,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=100,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=540,
    )
    later = VisitAssignment(
        id=2,
        requested_date=DAY,
        duration_minutes=60,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=200,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=600,
    )
    verifier.verify_that(driving_time_gap_between_proposed_visits_fallback).given(
        earlier, later
    ).penalizes(0)


def test_gap_to_existing_assignment_smaller_than_driving_time_is_penalized(
    verifier: ConstraintVerifier,
) -> None:
    proposed = _visit(1, start_minutes=540, duration_minutes=60, location_id=100)
    existing = ExistingAssignmentFact(
        id="e1",
        employee=EMPLOYEE,
        requested_date=DAY,
        start_minutes=610,
        end_minutes=670,
        location_id=200,
        latitude=52.0,
        longitude=5.0,
    )
    driving_time = DrivingTimeFact(
        origin_kind="customer_location",
        origin_id=100,
        destination_kind="customer_location",
        destination_id=200,
        duration_minutes=20,
    )
    verifier.verify_that(driving_time_gap_to_existing_assignment).given(
        proposed, existing, driving_time
    ).penalizes(1)


def test_gap_to_existing_assignment_equal_to_driving_time_is_not_penalized(
    verifier: ConstraintVerifier,
) -> None:
    proposed = _visit(1, start_minutes=540, duration_minutes=60, location_id=100)
    existing = ExistingAssignmentFact(
        id="e1",
        employee=EMPLOYEE,
        requested_date=DAY,
        start_minutes=620,
        end_minutes=680,
        location_id=200,
        latitude=52.0,
        longitude=5.0,
    )
    driving_time = DrivingTimeFact(
        origin_kind="customer_location",
        origin_id=100,
        destination_kind="customer_location",
        destination_id=200,
        duration_minutes=20,
    )
    verifier.verify_that(driving_time_gap_to_existing_assignment).given(
        proposed, existing, driving_time
    ).penalizes(0)


def test_gap_to_existing_assignment_fallback_smaller_than_estimate_is_penalized(
    verifier: ConstraintVerifier,
) -> None:
    proposed = VisitAssignment(
        id=1,
        requested_date=DAY,
        duration_minutes=60,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=100,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=540,
    )
    existing = ExistingAssignmentFact(
        id="e1",
        employee=EMPLOYEE,
        requested_date=DAY,
        start_minutes=601,
        end_minutes=661,
        location_id=200,
        latitude=52.1,
        longitude=5.1,
    )
    verifier.verify_that(driving_time_gap_to_existing_assignment_fallback).given(
        proposed, existing
    ).penalizes(1)


def test_first_visit_before_home_drive_completes_is_penalized(verifier: ConstraintVerifier) -> None:
    schedule = EmployeeDaySchedule(employee_id=1, date=DAY, start_minutes=480, end_minutes=1000)
    # Working hours start at 08:00 (480); a 20-minute home drive means the
    # first visit can't start before 08:20 (500) - this one starts at 08:10.
    first_visit = _visit(1, start_minutes=490, duration_minutes=60, location_id=100)
    driving_time = DrivingTimeFact(
        origin_kind="employee",
        origin_id=1,
        destination_kind="customer_location",
        destination_id=100,
        duration_minutes=20,
    )
    verifier.verify_that(driving_time_gap_before_first_visit).given(
        first_visit, schedule, driving_time
    ).penalizes(1)


def test_first_visit_at_or_after_home_drive_completes_is_not_penalized(
    verifier: ConstraintVerifier,
) -> None:
    schedule = EmployeeDaySchedule(employee_id=1, date=DAY, start_minutes=480, end_minutes=1000)
    first_visit = _visit(1, start_minutes=500, duration_minutes=60, location_id=100)
    driving_time = DrivingTimeFact(
        origin_kind="employee",
        origin_id=1,
        destination_kind="customer_location",
        destination_id=100,
        duration_minutes=20,
    )
    verifier.verify_that(driving_time_gap_before_first_visit).given(
        first_visit, schedule, driving_time
    ).penalizes(0)


def test_first_visit_fallback_before_home_drive_completes_is_penalized(
    verifier: ConstraintVerifier,
) -> None:
    schedule = EmployeeDaySchedule(employee_id=1, date=DAY, start_minutes=480, end_minutes=1000)
    first_visit = VisitAssignment(
        id=1,
        requested_date=DAY,
        duration_minutes=60,
        required_product_ids=frozenset(),
        region_id=1,
        location_id=100,
        latitude=52.1,
        longitude=5.1,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=481,
    )
    verifier.verify_that(driving_time_gap_before_first_visit_fallback).given(
        first_visit, schedule
    ).penalizes(1)
