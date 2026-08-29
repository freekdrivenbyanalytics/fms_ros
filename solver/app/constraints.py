from math import asin, cos, radians, sin, sqrt

from timefold.solver.score import (
    Constraint,
    ConstraintFactory,
    HardMediumSoftScore,
    Joiners,
    constraint_provider,
)

from app.domain import ExistingAssignmentFact, VisitAssignment

# Travel-distance penalties are pairwise proximity, not a literal route/path
# length: every pair of same-employee-same-day visits (proposed and/or
# existing) contributes its distance to the soft score. This prefers spatially
# clustered schedules without modeling a specific visiting order.
_DISTANCE_WEIGHT_PER_KM = 10


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def _is_scheduled(visit: VisitAssignment) -> bool:
    return visit.employee is not None and visit.start_minutes is not None


def _is_unassigned(visit: VisitAssignment) -> bool:
    return not _is_scheduled(visit)


def _missing_skills(visit: VisitAssignment) -> bool:
    return _is_scheduled(visit) and not visit.required_skill_ids.issubset(visit.employee.skill_ids)


def _wrong_region(visit: VisitAssignment) -> bool:
    return _is_scheduled(visit) and visit.region_id not in visit.employee.region_ids


def _outside_working_hours(visit: VisitAssignment) -> bool:
    if not _is_scheduled(visit):
        return False
    return (
        visit.start_minutes < visit.employee.work_start_minutes
        or visit.end_minutes() > visit.employee.work_end_minutes
    )


def _both_scheduled(a: VisitAssignment, b: VisitAssignment) -> bool:
    return _is_scheduled(a) and _is_scheduled(b)


def _visit_distance_km(a: VisitAssignment, b: VisitAssignment) -> int:
    return int(_haversine_km(a.latitude, a.longitude, b.latitude, b.longitude) * _DISTANCE_WEIGHT_PER_KM)


def _visit_existing_distance_km(visit: VisitAssignment, existing: ExistingAssignmentFact) -> int:
    return int(
        _haversine_km(visit.latitude, visit.longitude, existing.latitude, existing.longitude)
        * _DISTANCE_WEIGHT_PER_KM
    )


@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory) -> list[Constraint]:
    same_employee_same_date = [
        Joiners.equal(lambda v: v.employee),
        Joiners.equal(lambda v: v.requested_date),
    ]
    same_employee_same_date_cross = [
        Joiners.equal(lambda v: v.employee, lambda e: e.employee),
        Joiners.equal(lambda v: v.requested_date, lambda e: e.requested_date),
    ]

    return [
        # Medium: prefer scheduling every visit over leaving it unassigned.
        constraint_factory.for_each_including_unassigned(VisitAssignment)
        .filter(_is_unassigned)
        .penalize(HardMediumSoftScore.ONE_MEDIUM)
        .as_constraint("Unscheduled visit"),
        # Hard constraints.
        constraint_factory.for_each(VisitAssignment)
        .filter(_missing_skills)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Missing required skill"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_wrong_region)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Employee not scoped to region"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_outside_working_hours)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Outside working hours"),
        constraint_factory.for_each_unique_pair(
            VisitAssignment,
            *same_employee_same_date,
            Joiners.overlapping(lambda v: v.start_minutes, lambda v: v.end_minutes()),
        )
        .filter(_both_scheduled)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Overlapping proposed visits"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(
            ExistingAssignmentFact,
            *same_employee_same_date_cross,
            Joiners.overlapping(
                lambda v: v.start_minutes,
                lambda v: v.end_minutes(),
                lambda e: e.start_minutes,
                lambda e: e.end_minutes,
            ),
        )
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Overlapping existing assignment"),
        # Soft: minimize total pairwise travel distance per employee per day.
        constraint_factory.for_each_unique_pair(VisitAssignment, *same_employee_same_date)
        .filter(_both_scheduled)
        .penalize(HardMediumSoftScore.ONE_SOFT, _visit_distance_km)
        .as_constraint("Travel distance between proposed visits"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(ExistingAssignmentFact, *same_employee_same_date_cross)
        .penalize(HardMediumSoftScore.ONE_SOFT, _visit_existing_distance_km)
        .as_constraint("Travel distance to existing assignment"),
    ]
