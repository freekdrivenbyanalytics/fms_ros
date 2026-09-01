from app.constraints import define_constraints
from app.domain import (
    Employee,
    EmployeeDaySchedule,
    ExistingAssignmentFact,
    Schedule,
    VisitAssignment,
    default_start_time_range,
)
from app.schemas import DEFAULT_TIME_LIMIT_SECONDS, OptimizeRequest, OptimizeResponse, ScheduledVisitOut
from timefold.solver import SolverFactory
from timefold.solver.config import Duration, ScoreDirectorFactoryConfig, SolverConfig, TerminationConfig


def _build_schedule(request: OptimizeRequest) -> Schedule:
    employees_by_id = {
        e.id: Employee(
            id=e.id,
            skill_ids=frozenset(e.skill_ids),
            region_ids=frozenset(e.region_ids),
            latitude=e.latitude,
            longitude=e.longitude,
        )
        for e in request.employees
    }

    employee_day_schedules = [
        EmployeeDaySchedule(
            employee_id=s.employee_id,
            date=s.date,
            start_minutes=s.start_minutes,
            end_minutes=s.end_minutes,
        )
        for s in request.employee_day_schedules
    ]

    existing_assignments = [
        ExistingAssignmentFact(
            id=a.id,
            employee=employees_by_id[a.employee_id],
            requested_date=a.requested_date,
            start_minutes=a.start_minutes,
            end_minutes=a.end_minutes,
            latitude=a.latitude,
            longitude=a.longitude,
        )
        for a in request.existing_assignments
    ]

    visits = [
        VisitAssignment(
            id=v.id,
            requested_date=v.requested_date,
            duration_minutes=v.duration_minutes,
            required_skill_ids=frozenset(v.required_skill_ids),
            region_id=v.region_id,
            latitude=v.latitude,
            longitude=v.longitude,
        )
        for v in request.visits
    ]

    return Schedule(
        employees=list(employees_by_id.values()),
        employee_day_schedules=employee_day_schedules,
        existing_assignments=existing_assignments,
        start_times=default_start_time_range(),
        visits=visits,
    )


def solve_schedule(request: OptimizeRequest) -> OptimizeResponse:
    time_limit_seconds = request.time_limit_seconds or DEFAULT_TIME_LIMIT_SECONDS
    # `spent_limit` alone runs the full budget even once the best score stops
    # improving. `unimproved_spent_limit` lets small problems finish quickly
    # while `spent_limit` still bounds worst-case runtime for larger ones.
    unimproved_seconds = min(1, time_limit_seconds)

    solver_config = SolverConfig(
        solution_class=Schedule,
        entity_class_list=[VisitAssignment],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=define_constraints
        ),
        termination_config=TerminationConfig(
            spent_limit=Duration(seconds=time_limit_seconds),
            unimproved_spent_limit=Duration(seconds=unimproved_seconds),
        ),
    )

    problem = _build_schedule(request)
    solver = SolverFactory.create(solver_config).build_solver()
    solution = solver.solve(problem)

    scheduled: list[ScheduledVisitOut] = []
    unscheduled_visit_ids: list[int] = []
    for visit in solution.visits:
        if visit.employee is None or visit.start_minutes is None:
            unscheduled_visit_ids.append(visit.id)
        else:
            scheduled.append(
                ScheduledVisitOut(
                    visit_id=visit.id,
                    employee_id=visit.employee.id,
                    start_minutes=visit.start_minutes,
                    end_minutes=visit.end_minutes(),
                )
            )

    return OptimizeResponse(scheduled=scheduled, unscheduled_visit_ids=unscheduled_visit_ids)
