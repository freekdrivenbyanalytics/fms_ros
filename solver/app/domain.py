from app.jvm import ensure_jvm_env

ensure_jvm_env()

from dataclasses import dataclass, field
from datetime import date
# Aliased for VisitAssignment.date's own annotation only: `date: Annotated[date
# | None, ...] = field(...)` would otherwise self-shadow, since the default
# value gets bound to the class-body name `date` before that same line's
# annotation expression is evaluated.
from datetime import date as _Date
from typing import Annotated

from timefold.solver.domain import (
    PlanningEntityCollectionProperty,
    PlanningId,
    PlanningScore,
    PlanningVariable,
    ProblemFactCollectionProperty,
    ValueRangeProvider,
    planning_entity,
    planning_solution,
)
from timefold.solver.score import HardMediumSoftScore

# 06:00-20:00 in 15-minute increments, shared candidate start times for every visit.
START_TIME_STEP_MINUTES = 15
START_TIME_WINDOW = (6 * 60, 20 * 60)


def default_start_time_range() -> list[int]:
    start, end = START_TIME_WINDOW
    return list(range(start, end + 1, START_TIME_STEP_MINUTES))


@dataclass(frozen=True)
class Employee:
    id: Annotated[int, PlanningId]
    employee_skill_ids: frozenset
    region_ids: frozenset
    latitude: float
    longitude: float


@dataclass(frozen=True)
class EmployeeDaySchedule:
    """An employee's resolved working-hours window for one date. Not a value
    range - just data the constraints join against. Absence of a fact for a
    given (employee_id, date) means the employee has no schedule that date."""

    employee_id: int
    date: date
    start_minutes: int
    end_minutes: int


@dataclass(frozen=True)
class ExistingAssignmentFact:
    """A locked (pinned or already-started) assignment. `date` is the date
    this assignment actually occupies (its planned_start's date) - not the
    visit's nominal requested_date, which can differ once a visit has been
    rescheduled."""

    id: Annotated[str, PlanningId]
    employee: Employee
    date: date
    start_minutes: int
    end_minutes: int
    location_id: int
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DrivingTimeFact:
    """A static, region-scoped driving time (minutes) from one location
    endpoint to another. origin/destination are (kind, id) pairs since they
    may reference either a customer location or an employee's home
    location - two separate id spaces."""

    origin_kind: str
    origin_id: int
    destination_kind: str
    destination_id: int
    duration_minutes: int


@planning_entity
@dataclass
class VisitAssignment:
    id: Annotated[int, PlanningId]
    # Fixed nominal (contract-cadence) date - never mutated. Used only as the
    # preference anchor for the "stay close to your own schedule" soft
    # constraint; "same day" grouping (double-booking, driving-time gaps,
    # working-hours lookups) uses the `date` planning variable below instead.
    requested_date: date
    duration_minutes: int
    required_skill_ids: frozenset
    region_id: int
    location_id: int
    latitude: float
    longitude: float
    priority: int
    days_until_due: int
    # Same value on every visit in a run (the run's total visit count) - lets
    # the "Unscheduled visit" constraint size its priority-tier weighting to
    # this run's actual scale. See constraints.py's _unscheduled_priority_weight.
    total_visit_count: int
    # Nominal days between this visit's requested_date and its contract
    # line's immediately preceding occurrence's requested_date - None if
    # there is no preceding occurrence. Paired with exactly one of
    # previous_visit_id/previous_actual_date below.
    interval_days: int | None = field(default=None)
    # The preceding occurrence, when it's also a candidate in this same run
    # (so its own `date` is being jointly decided too).
    previous_visit_id: int | None = field(default=None)
    # The preceding occurrence's actual date, when it's fixed (a locked
    # assignment) rather than a candidate in this run.
    previous_actual_date: date | None = field(default=None)
    employee: Annotated[
        Employee | None,
        PlanningVariable(value_range_provider_refs=["employee_range"], allows_unassigned=True),
    ] = field(default=None)
    start_minutes: Annotated[
        int | None,
        PlanningVariable(value_range_provider_refs=["start_time_range"], allows_unassigned=True),
    ] = field(default=None)
    # The chosen date - bounded to the run's scheduling window (see
    # Schedule.candidate_dates), never earlier than today.
    date: Annotated[
        _Date | None,
        PlanningVariable(value_range_provider_refs=["date_range"], allows_unassigned=True),
    ] = field(default=None)

    def end_minutes(self) -> int | None:
        if self.start_minutes is None:
            return None
        return self.start_minutes + self.duration_minutes

    def is_unassigned(self) -> bool:
        return self.employee is None or self.start_minutes is None or self.date is None


@planning_solution
@dataclass
class Schedule:
    employees: Annotated[
        list[Employee], ProblemFactCollectionProperty, ValueRangeProvider(id="employee_range")
    ]
    employee_day_schedules: Annotated[list[EmployeeDaySchedule], ProblemFactCollectionProperty]
    existing_assignments: Annotated[list[ExistingAssignmentFact], ProblemFactCollectionProperty]
    driving_times: Annotated[list[DrivingTimeFact], ProblemFactCollectionProperty]
    start_times: Annotated[list[int], ValueRangeProvider(id="start_time_range")]
    candidate_dates: Annotated[list[date], ValueRangeProvider(id="date_range")]
    visits: Annotated[list[VisitAssignment], PlanningEntityCollectionProperty]
    score: Annotated[HardMediumSoftScore | None, PlanningScore] = field(default=None)
