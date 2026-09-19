from datetime import date, timedelta

import pytest
from app.constraints import _NOMINAL_DATE_WEIGHT_PER_DAY, define_constraints, nominal_date_drift
from app.domain import Employee, Schedule, VisitAssignment
from timefold.solver.test import ConstraintVerifier

REQUESTED_DATE = date(2026, 1, 5)

EMPLOYEE = Employee(
    id=1,
    employee_skill_ids=frozenset(),
    region_ids=frozenset({1}),
    latitude=52.0,
    longitude=5.0,
)


def _visit(chosen_date: date) -> VisitAssignment:
    return VisitAssignment(
        id=1,
        requested_date=REQUESTED_DATE,
        duration_minutes=60,
        required_skill_ids=frozenset(),
        region_id=1,
        location_id=100,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
        employee=EMPLOYEE,
        start_minutes=480,
        date=chosen_date,
    )


@pytest.fixture(scope="module")
def verifier() -> ConstraintVerifier:
    return ConstraintVerifier.build(define_constraints, Schedule, VisitAssignment)


def test_no_drift_is_not_penalized(verifier: ConstraintVerifier) -> None:
    verifier.verify_that(nominal_date_drift).given(_visit(REQUESTED_DATE)).penalizes_by(0)


def test_drift_later_is_penalized_proportionally(verifier: ConstraintVerifier) -> None:
    verifier.verify_that(nominal_date_drift).given(
        _visit(REQUESTED_DATE + timedelta(days=3))
    ).penalizes_by(3 * _NOMINAL_DATE_WEIGHT_PER_DAY)


def test_drift_earlier_is_penalized_proportionally(verifier: ConstraintVerifier) -> None:
    verifier.verify_that(nominal_date_drift).given(
        _visit(REQUESTED_DATE - timedelta(days=2))
    ).penalizes_by(2 * _NOMINAL_DATE_WEIGHT_PER_DAY)


def test_unassigned_visit_is_not_penalized(verifier: ConstraintVerifier) -> None:
    unassigned = VisitAssignment(
        id=1,
        requested_date=REQUESTED_DATE,
        duration_minutes=60,
        required_skill_ids=frozenset(),
        region_id=1,
        location_id=100,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=1,
    )
    verifier.verify_that(nominal_date_drift).given(unassigned).penalizes_by(0)
