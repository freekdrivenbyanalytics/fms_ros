from app.constraints import define_constraints
from app.domain import (
    DrivingTimeFact,
    Employee,
    EmployeeDaySchedule,
    ExistingAssignmentFact,
    Schedule,
    VisitAssignment,
    default_start_time_range,
)
from app.schemas import DEFAULT_TIME_LIMIT_SECONDS, OptimizeRequest, OptimizeResponse, ScheduledVisitOut
from timefold.solver import SolverFactory
from timefold.solver.config import (
    Duration,
    EnvironmentMode,
    ScoreDirectorFactoryConfig,
    SolverConfig,
    TerminationConfig,
)


def _build_schedule(request: OptimizeRequest) -> Schedule:
    employees_by_id = {
        e.id: Employee(
            id=e.id,
            employee_skill_ids=frozenset(e.employee_skill_ids),
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
            location_id=a.location_id,
            latitude=a.latitude,
            longitude=a.longitude,
        )
        for a in request.existing_assignments
    ]

    total_visit_count = len(request.visits)
    visits = [
        VisitAssignment(
            id=v.id,
            requested_date=v.requested_date,
            duration_minutes=v.duration_minutes,
            required_skill_ids=frozenset(v.required_skill_ids),
            region_id=v.region_id,
            location_id=v.location_id,
            latitude=v.latitude,
            longitude=v.longitude,
            priority=v.priority,
            days_until_due=v.days_until_due,
            total_visit_count=total_visit_count,
        )
        for v in request.visits
    ]

    driving_times = [
        DrivingTimeFact(
            origin_kind=d.origin_kind,
            origin_id=d.origin_id,
            destination_kind=d.destination_kind,
            destination_id=d.destination_id,
            duration_minutes=d.duration_minutes,
        )
        for d in request.driving_times
    ]

    return Schedule(
        employees=list(employees_by_id.values()),
        employee_day_schedules=employee_day_schedules,
        existing_assignments=existing_assignments,
        driving_times=driving_times,
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
        # The Timefold Python package defaults to PHASE_ASSERT (full
        # score-corruption checking - recalculates the whole score from
        # scratch every phase) when this isn't set, which is a constraint
        # -development debugging aid, not something to run in production:
        # it makes every phase transition roughly as expensive as a full
        # solve. NO_ASSERT drops that overhead (the Java engine also has a
        # REPRODUCIBLE mode between the two, but this Python binding doesn't
        # expose it); constraint-stream correctness is covered by the
        # ConstraintVerifier unit tests in solver/tests instead.
        environment_mode=EnvironmentMode.NO_ASSERT,
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
