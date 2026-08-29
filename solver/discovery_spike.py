import os
from dataclasses import dataclass, field
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
from timefold.solver.score import Constraint, ConstraintFactory, HardSoftScore, constraint_provider


@dataclass(frozen=True)
class Employee:
    id: Annotated[str, PlanningId]
    name: str


@planning_entity
@dataclass
class VisitAssignment:
    id: Annotated[str, PlanningId]
    employee: Annotated[
        Employee | None, PlanningVariable(value_range_provider_refs=["employee_range"])
    ] = field(default=None)


@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory) -> list[Constraint]:
    return [
        constraint_factory.for_each(VisitAssignment)
        .filter(lambda visit: visit.id == "visit-2" and visit.employee is not None and visit.employee.id == "alice")
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("alice cannot take visit-2"),
    ]


@planning_solution
@dataclass
class Schedule:
    employees: Annotated[
        list[Employee], ProblemFactCollectionProperty, ValueRangeProvider(id="employee_range")
    ]
    visits: Annotated[list[VisitAssignment], PlanningEntityCollectionProperty]
    score: Annotated[HardSoftScore | None, PlanningScore] = field(default=None)


def main() -> None:
    solver_config = SolverConfig(
        solution_class=Schedule,
        entity_class_list=[VisitAssignment],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=define_constraints
        ),
        termination_config=TerminationConfig(spent_limit=Duration(seconds=5)),
    )

    alice = Employee(id="alice", name="Alice")
    bob = Employee(id="bob", name="Bob")
    problem = Schedule(
        employees=[alice, bob],
        visits=[VisitAssignment(id="visit-1"), VisitAssignment(id="visit-2")],
    )

    solver = SolverFactory.create(solver_config).build_solver()
    solution = solver.solve(problem)

    print("score:", solution.score)
    for visit in solution.visits:
        print(f"  {visit.id} -> {visit.employee.id if visit.employee else None}")


if __name__ == "__main__":
    main()
