import os
from dataclasses import dataclass, field
from datetime import date
from typing import Annotated

import jdk4py

os.environ["JAVA_HOME"] = str(jdk4py.JAVA_HOME)
os.environ["PATH"] = str(jdk4py.JAVA_HOME / "bin") + os.pathsep + os.environ["PATH"]

from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)
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
from timefold.solver.score import (
    Constraint,
    ConstraintFactory,
    HardMediumSoftScore,
    Joiners,
    constraint_provider,
)


def is_unassigned(visit: "VisitAssignment") -> bool:
    return visit.employee is None or visit.start_minutes is None

START_TIMES = list(range(6 * 60, 20 * 60 + 1, 15))  # 06:00..20:00 in 15-min steps


@dataclass(frozen=True)
class Employee:
    id: Annotated[str, PlanningId]
    work_start_minutes: int
    work_end_minutes: int
    skill_ids: frozenset
    region_ids: frozenset
    latitude: float
    longitude: float


@planning_entity
@dataclass
class VisitAssignment:
    id: Annotated[str, PlanningId]
    requested_date: date
    duration_minutes: int
    required_skill_ids: frozenset
    region_id: str
    latitude: float
    longitude: float
    employee: Annotated[
        Employee | None, PlanningVariable(value_range_provider_refs=["employee_range"], allows_unassigned=True)
    ] = field(default=None)
    start_minutes: Annotated[
        int | None, PlanningVariable(value_range_provider_refs=["start_time_range"], allows_unassigned=True)
    ] = field(default=None)

    def end_minutes(self):
        if self.start_minutes is None:
            return None
        return self.start_minutes + self.duration_minutes


def missing_skills(visit: VisitAssignment) -> bool:
    return visit.employee is not None and not visit.required_skill_ids.issubset(visit.employee.skill_ids)


def wrong_region(visit: VisitAssignment) -> bool:
    return visit.employee is not None and visit.region_id not in visit.employee.region_ids


def outside_working_hours(visit: VisitAssignment) -> bool:
    if visit.employee is None or visit.start_minutes is None:
        return False
    return (
        visit.start_minutes < visit.employee.work_start_minutes
        or visit.end_minutes() > visit.employee.work_end_minutes
    )


def haversine_km(a: VisitAssignment, b: VisitAssignment) -> float:
    from math import asin, cos, radians, sin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, [a.latitude, a.longitude, b.latitude, b.longitude])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory) -> list[Constraint]:
    both_assigned_same_employee_same_date = [
        Joiners.equal(lambda v: v.employee),
        Joiners.equal(lambda v: v.requested_date),
    ]

    return [
        constraint_factory.for_each_including_unassigned(VisitAssignment)
        .filter(is_unassigned)
        .penalize(HardMediumSoftScore.ONE_MEDIUM)
        .as_constraint("prefer assigning every visit"),
        constraint_factory.for_each(VisitAssignment)
        .filter(missing_skills)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("missing skills"),
        constraint_factory.for_each(VisitAssignment)
        .filter(wrong_region)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("wrong region"),
        constraint_factory.for_each(VisitAssignment)
        .filter(outside_working_hours)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("outside working hours"),
        constraint_factory.for_each_unique_pair(
            VisitAssignment,
            *both_assigned_same_employee_same_date,
            Joiners.overlapping(lambda v: v.start_minutes, lambda v: v.end_minutes()),
        )
        .filter(lambda a, b: a.employee is not None and a.start_minutes is not None and b.start_minutes is not None)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("overlapping visits for same employee"),
        constraint_factory.for_each_unique_pair(VisitAssignment, *both_assigned_same_employee_same_date)
        .filter(lambda a, b: a.employee is not None and a.start_minutes is not None and b.start_minutes is not None)
        .penalize(HardMediumSoftScore.ONE_SOFT, lambda a, b: int(haversine_km(a, b) * 10))
        .as_constraint("minimize pairwise travel distance"),
    ]


@planning_solution
@dataclass
class Schedule:
    employees: Annotated[
        list[Employee], ProblemFactCollectionProperty, ValueRangeProvider(id="employee_range")
    ]
    start_times: Annotated[list[int], ValueRangeProvider(id="start_time_range")]
    visits: Annotated[list[VisitAssignment], PlanningEntityCollectionProperty]
    score: Annotated[HardMediumSoftScore | None, PlanningScore] = field(default=None)


def main() -> None:
    alice = Employee(
        id="alice",
        work_start_minutes=8 * 60,
        work_end_minutes=16 * 60,
        skill_ids=frozenset({"plumbing"}),
        region_ids=frozenset({"utrecht"}),
        latitude=52.09,
        longitude=5.12,
    )
    bob = Employee(
        id="bob",
        work_start_minutes=9 * 60,
        work_end_minutes=17 * 60,
        skill_ids=frozenset({"plumbing", "electrical"}),
        region_ids=frozenset({"utrecht"}),
        latitude=52.10,
        longitude=5.10,
    )

    visit1 = VisitAssignment(
        id="visit-1",
        requested_date=date(2026, 9, 1),
        duration_minutes=60,
        required_skill_ids=frozenset({"electrical"}),
        region_id="utrecht",
        latitude=52.091,
        longitude=5.121,
    )
    visit2 = VisitAssignment(
        id="visit-2",
        requested_date=date(2026, 9, 1),
        duration_minutes=60,
        required_skill_ids=frozenset({"plumbing"}),
        region_id="utrecht",
        latitude=52.095,
        longitude=5.125,
    )

    solver_config = SolverConfig(
        solution_class=Schedule,
        entity_class_list=[VisitAssignment],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=define_constraints
        ),
        termination_config=TerminationConfig(spent_limit=Duration(seconds=5)),
    )

    problem = Schedule(employees=[alice, bob], start_times=START_TIMES, visits=[visit1, visit2])
    solver = SolverFactory.create(solver_config).build_solver()
    solution = solver.solve(problem)

    print("score:", solution.score)
    for v in solution.visits:
        emp = v.employee.id if v.employee else None
        start = f"{v.start_minutes // 60:02d}:{v.start_minutes % 60:02d}" if v.start_minutes is not None else None
        print(f"  {v.id} -> employee={emp} start={start}")


if __name__ == "__main__":
    main()
