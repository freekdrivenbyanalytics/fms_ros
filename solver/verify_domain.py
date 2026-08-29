from datetime import date

from app.domain import Employee, ExistingAssignmentFact, Schedule, VisitAssignment, default_start_time_range
from app.constraints import define_constraints
from timefold.solver import SolverFactory
from timefold.solver.config import Duration, ScoreDirectorFactoryConfig, SolverConfig, TerminationConfig


def main() -> None:
    alice = Employee(
        id=1,
        work_start_minutes=8 * 60,
        work_end_minutes=16 * 60,
        skill_ids=frozenset({"plumbing"}),
        region_ids=frozenset({1}),
        latitude=52.09,
        longitude=5.12,
    )
    bob = Employee(
        id=2,
        work_start_minutes=9 * 60,
        work_end_minutes=17 * 60,
        skill_ids=frozenset({"plumbing", "electrical"}),
        region_ids=frozenset({1}),
        latitude=52.10,
        longitude=5.10,
    )

    existing = ExistingAssignmentFact(
        id="assignment-99",
        employee=bob,
        requested_date=date(2026, 9, 1),
        start_minutes=9 * 60,
        end_minutes=10 * 60,
        latitude=52.101,
        longitude=5.101,
    )

    visit1 = VisitAssignment(
        id=1,
        requested_date=date(2026, 9, 1),
        duration_minutes=60,
        required_skill_ids=frozenset({"electrical"}),
        region_id=1,
        latitude=52.091,
        longitude=5.121,
    )
    # Deliberately overlaps `existing` in time if bob were also chosen for it,
    # to exercise the cross-class overlap constraint against a problem fact.
    visit2 = VisitAssignment(
        id=2,
        requested_date=date(2026, 9, 1),
        duration_minutes=60,
        required_skill_ids=frozenset({"plumbing"}),
        region_id=1,
        latitude=52.095,
        longitude=5.125,
    )
    visit3 = VisitAssignment(
        id=3,
        requested_date=date(2026, 9, 1),
        duration_minutes=45,
        required_skill_ids=frozenset({"welding"}),  # nobody has this skill
        region_id=1,
        latitude=52.096,
        longitude=5.126,
    )

    solver_config = SolverConfig(
        solution_class=Schedule,
        entity_class_list=[VisitAssignment],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=define_constraints
        ),
        termination_config=TerminationConfig(spent_limit=Duration(seconds=5)),
    )

    problem = Schedule(
        employees=[alice, bob],
        existing_assignments=[existing],
        start_times=default_start_time_range(),
        visits=[visit1, visit2, visit3],
    )
    solver = SolverFactory.create(solver_config).build_solver()
    solution = solver.solve(problem)

    print("score:", solution.score)
    for v in solution.visits:
        emp = v.employee.id if v.employee else None
        start = f"{v.start_minutes // 60:02d}:{v.start_minutes % 60:02d}" if v.start_minutes is not None else None
        print(f"  visit={v.id} employee={emp} start={start}")


if __name__ == "__main__":
    main()
