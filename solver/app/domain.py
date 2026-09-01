from app.jvm import ensure_jvm_env

ensure_jvm_env()

from dataclasses import dataclass, field
from datetime import date
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
    skill_ids: frozenset
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
    id: Annotated[str, PlanningId]
    employee: Employee
    requested_date: date
    start_minutes: int
    end_minutes: int
    latitude: float
    longitude: float


@planning_entity
@dataclass
class VisitAssignment:
    id: Annotated[int, PlanningId]
    requested_date: date
    duration_minutes: int
    required_skill_ids: frozenset
    region_id: int
    latitude: float
    longitude: float
    employee: Annotated[
        Employee | None,
        PlanningVariable(value_range_provider_refs=["employee_range"], allows_unassigned=True),
    ] = field(default=None)
    start_minutes: Annotated[
        int | None,
        PlanningVariable(value_range_provider_refs=["start_time_range"], allows_unassigned=True),
    ] = field(default=None)

    def end_minutes(self) -> int | None:
        if self.start_minutes is None:
            return None
        return self.start_minutes + self.duration_minutes

    def is_unassigned(self) -> bool:
        return self.employee is None or self.start_minutes is None


@planning_solution
@dataclass
class Schedule:
    employees: Annotated[
        list[Employee], ProblemFactCollectionProperty, ValueRangeProvider(id="employee_range")
    ]
    employee_day_schedules: Annotated[list[EmployeeDaySchedule], ProblemFactCollectionProperty]
    existing_assignments: Annotated[list[ExistingAssignmentFact], ProblemFactCollectionProperty]
    start_times: Annotated[list[int], ValueRangeProvider(id="start_time_range")]
    visits: Annotated[list[VisitAssignment], PlanningEntityCollectionProperty]
    score: Annotated[HardMediumSoftScore | None, PlanningScore] = field(default=None)
