from datetime import date, timedelta

import pytest
from app.constraints import (
    _INTERVAL_SHORTFALL_WEIGHT_PER_DAY,
    define_constraints,
    interval_since_previous_occurrence_existing,
    interval_since_previous_occurrence_sibling,
)
from app.domain import Employee, Schedule, VisitAssignment
from timefold.solver.test import ConstraintVerifier

REQUESTED_DATE = date(2026, 1, 19)
INTERVAL_DAYS = 14

EMPLOYEE = Employee(
    id=1,
    employee_skill_ids=frozenset(),
    region_ids=frozenset({1}),
    latitude=52.0,
    longitude=5.0,
)


def _visit(
    visit_id: int,
    chosen_date: date,
    *,
    interval_days: int | None = INTERVAL_DAYS,
    previous_visit_id: int | None = None,
    previous_actual_date: date | None = None,
) -> VisitAssignment:
    return VisitAssignment(
        id=visit_id,
        requested_date=REQUESTED_DATE,
        duration_minutes=60,
        required_skill_ids=frozenset(),
        region_id=1,
        location_id=100 + visit_id,
        latitude=52.0,
        longitude=5.0,
        priority=2,
        days_until_due=0,
        total_visit_count=2,
        employee=EMPLOYEE,
        start_minutes=480,
        date=chosen_date,
        interval_days=interval_days,
        previous_visit_id=previous_visit_id,
        previous_actual_date=previous_actual_date,
    )


@pytest.fixture(scope="module")
def verifier() -> ConstraintVerifier:
    return ConstraintVerifier.build(define_constraints, Schedule, VisitAssignment)


# --- sibling variant: previous occurrence is also a candidate this run ---


def test_sibling_interval_respected_is_not_penalized(verifier: ConstraintVerifier) -> None:
    previous = _visit(1, date(2026, 1, 5))
    current = _visit(
        2, date(2026, 1, 19), previous_visit_id=1  # exactly 14 days after previous
    )
    verifier.verify_that(interval_since_previous_occurrence_sibling).given(
        current, previous
    ).penalizes_by(0)


def test_sibling_interval_shortfall_is_penalized_proportionally(
    verifier: ConstraintVerifier,
) -> None:
    previous = _visit(1, date(2026, 1, 5))
    # Only 10 days after previous instead of the requested 14 - a 4-day shortfall.
    current = _visit(2, date(2026, 1, 15), previous_visit_id=1)
    verifier.verify_that(interval_since_previous_occurrence_sibling).given(
        current, previous
    ).penalizes_by(4 * _INTERVAL_SHORTFALL_WEIGHT_PER_DAY)


def test_sibling_interval_exceeded_is_not_penalized(verifier: ConstraintVerifier) -> None:
    previous = _visit(1, date(2026, 1, 5))
    current = _visit(2, date(2026, 1, 25), previous_visit_id=1)  # 20 days later
    verifier.verify_that(interval_since_previous_occurrence_sibling).given(
        current, previous
    ).penalizes_by(0)


def test_no_previous_visit_id_is_not_penalized(verifier: ConstraintVerifier) -> None:
    current = _visit(2, date(2026, 1, 6), previous_visit_id=None)
    other = _visit(1, date(2026, 1, 5))
    verifier.verify_that(interval_since_previous_occurrence_sibling).given(
        current, other
    ).penalizes_by(0)


def test_no_interval_days_is_not_penalized(verifier: ConstraintVerifier) -> None:
    previous = _visit(1, date(2026, 1, 5))
    current = _visit(2, date(2026, 1, 6), interval_days=None, previous_visit_id=1)
    verifier.verify_that(interval_since_previous_occurrence_sibling).given(
        current, previous
    ).penalizes_by(0)


# --- existing-assignment variant: previous occurrence is a locked fact ---


def test_existing_interval_respected_is_not_penalized(verifier: ConstraintVerifier) -> None:
    current = _visit(
        1, date(2026, 1, 19), previous_actual_date=date(2026, 1, 5)
    )
    verifier.verify_that(interval_since_previous_occurrence_existing).given(current).penalizes_by(0)


def test_existing_interval_shortfall_is_penalized_proportionally(
    verifier: ConstraintVerifier,
) -> None:
    current = _visit(
        1, date(2026, 1, 12), previous_actual_date=date(2026, 1, 5)  # 7 days, 7-day shortfall
    )
    verifier.verify_that(interval_since_previous_occurrence_existing).given(current).penalizes_by(
        7 * _INTERVAL_SHORTFALL_WEIGHT_PER_DAY
    )


def test_existing_no_previous_actual_date_is_not_penalized(verifier: ConstraintVerifier) -> None:
    current = _visit(1, date(2026, 1, 6), previous_actual_date=None)
    verifier.verify_that(interval_since_previous_occurrence_existing).given(current).penalizes_by(0)
