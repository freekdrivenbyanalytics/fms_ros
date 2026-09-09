from math import asin, cos, radians, sin, sqrt

from timefold.solver.score import (
    Constraint,
    ConstraintFactory,
    HardMediumSoftScore,
    Joiners,
    constraint_provider,
)

from app.domain import (
    DrivingTimeFact,
    EmployeeDaySchedule,
    ExistingAssignmentFact,
    VisitAssignment,
)

# Travel-time penalties are pairwise proximity, not a literal route/path: every
# pair of same-employee-same-day visits (proposed and/or existing), plus an
# employee's home-to-first-visit leg, contributes its driving time to the soft
# score. This prefers spatially/time-clustered schedules without modeling a
# specific visiting order.
_TIME_WEIGHT_PER_MINUTE = 10

# Only used when no computed DrivingTimeFact covers a leg (not yet computed,
# or a cross-region leg for a multi-region employee): converts Haversine
# distance to an estimated minutes figure so it's comparable to a real
# driving-time entry, rather than mixing a km-based and a minutes-based cost.
_ASSUMED_AVERAGE_SPEED_KMH = 40

_CUSTOMER_LOCATION = "customer_location"
_EMPLOYEE = "employee"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def _haversine_fallback_minutes(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    km = _haversine_km(lat1, lon1, lat2, lon2)
    return int(round(km / _ASSUMED_AVERAGE_SPEED_KMH * 60)) * _TIME_WEIGHT_PER_MINUTE


def _is_scheduled(visit: VisitAssignment) -> bool:
    return visit.employee is not None and visit.start_minutes is not None


def _is_unassigned(visit: VisitAssignment) -> bool:
    return not _is_scheduled(visit)


def _missing_products(visit: VisitAssignment) -> bool:
    return _is_scheduled(visit) and not visit.required_product_ids.issubset(
        visit.employee.product_ids
    )


def _wrong_region(visit: VisitAssignment) -> bool:
    return _is_scheduled(visit) and visit.region_id not in visit.employee.region_ids


def _outside_schedule_window(visit: VisitAssignment, schedule: EmployeeDaySchedule) -> bool:
    return (
        visit.start_minutes < schedule.start_minutes
        or visit.end_minutes() > schedule.end_minutes
    )


def _both_scheduled(a: VisitAssignment, b: VisitAssignment) -> bool:
    return _is_scheduled(a) and _is_scheduled(b)


def _earlier_location_id(a: VisitAssignment, b: VisitAssignment) -> int:
    return a.location_id if a.start_minutes <= b.start_minutes else b.location_id


def _later_location_id(a: VisitAssignment, b: VisitAssignment) -> int:
    return b.location_id if a.start_minutes <= b.start_minutes else a.location_id


def _pair_fallback_minutes(a: VisitAssignment, b: VisitAssignment) -> int:
    return _haversine_fallback_minutes(a.latitude, a.longitude, b.latitude, b.longitude)


def _earlier_location_id_existing(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    return v.location_id if v.start_minutes <= e.start_minutes else e.location_id


def _later_location_id_existing(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    return e.location_id if v.start_minutes <= e.start_minutes else v.location_id


def _existing_fallback_minutes(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    return _haversine_fallback_minutes(v.latitude, v.longitude, e.latitude, e.longitude)


def _employee_fallback_minutes(v: VisitAssignment) -> int:
    return _haversine_fallback_minutes(
        v.employee.latitude, v.employee.longitude, v.latitude, v.longitude
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
    visit_employee_id_same_date_schedule = [
        Joiners.equal(lambda v: v.employee.id, lambda s: s.employee_id),
        Joiners.equal(lambda v: v.requested_date, lambda s: s.date),
    ]
    # A visit's own driving-time leg to another location is always customer
    # location <-> customer location; an employee's home leg is always
    # employee -> customer location. These constant-valued joiners guard
    # against origin_id/destination_id collisions across the two independent
    # id spaces (a customer_location id and an employee id can coincide).
    pair_kind_joiners = [
        Joiners.equal(lambda a, b: _CUSTOMER_LOCATION, lambda dtf: dtf.origin_kind),
        Joiners.equal(lambda a, b: _CUSTOMER_LOCATION, lambda dtf: dtf.destination_kind),
    ]
    employee_leg_kind_joiners = [
        Joiners.equal(lambda v: _EMPLOYEE, lambda dtf: dtf.origin_kind),
        Joiners.equal(lambda v: _CUSTOMER_LOCATION, lambda dtf: dtf.destination_kind),
    ]
    first_visit_of_day_joiners = [
        Joiners.equal(lambda v: v.employee, lambda o: o.employee),
        Joiners.equal(lambda v: v.requested_date, lambda o: o.requested_date),
        Joiners.greater_than(lambda v: v.start_minutes, lambda o: o.start_minutes),
    ]

    return [
        # Medium: prefer scheduling every visit over leaving it unassigned.
        constraint_factory.for_each_including_unassigned(VisitAssignment)
        .filter(_is_unassigned)
        .penalize(HardMediumSoftScore.ONE_MEDIUM)
        .as_constraint("Unscheduled visit"),
        # Hard constraints.
        constraint_factory.for_each(VisitAssignment)
        .filter(_missing_products)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Missing required product"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_wrong_region)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Employee not scoped to region"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(EmployeeDaySchedule, *visit_employee_id_same_date_schedule)
        .filter(_outside_schedule_window)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Outside working hours"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .if_not_exists(EmployeeDaySchedule, *visit_employee_id_same_date_schedule)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("No resolved schedule for this date"),
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
        # Soft: minimize total pairwise travel time per employee per day,
        # using a computed driving-time entry when one covers the leg.
        constraint_factory.for_each_unique_pair(VisitAssignment, *same_employee_same_date)
        .filter(_both_scheduled)
        .join(
            DrivingTimeFact,
            *pair_kind_joiners,
            Joiners.equal(_earlier_location_id, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id, lambda dtf: dtf.destination_id),
        )
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda a, b, dtf: dtf.duration_minutes * _TIME_WEIGHT_PER_MINUTE,
        )
        .as_constraint("Travel time between proposed visits"),
        # ...and a Haversine-derived fallback when no such entry exists.
        constraint_factory.for_each_unique_pair(VisitAssignment, *same_employee_same_date)
        .filter(_both_scheduled)
        .if_not_exists(
            DrivingTimeFact,
            *pair_kind_joiners,
            Joiners.equal(_earlier_location_id, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id, lambda dtf: dtf.destination_id),
        )
        .penalize(HardMediumSoftScore.ONE_SOFT, _pair_fallback_minutes)
        .as_constraint("Travel time between proposed visits (fallback estimate)"),
        # Soft: same, but between a proposed visit and an existing fixed assignment.
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(ExistingAssignmentFact, *same_employee_same_date_cross)
        .join(
            DrivingTimeFact,
            *pair_kind_joiners,
            Joiners.equal(_earlier_location_id_existing, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id_existing, lambda dtf: dtf.destination_id),
        )
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda v, e, dtf: dtf.duration_minutes * _TIME_WEIGHT_PER_MINUTE,
        )
        .as_constraint("Travel time to existing assignment"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(ExistingAssignmentFact, *same_employee_same_date_cross)
        .if_not_exists(
            DrivingTimeFact,
            *pair_kind_joiners,
            Joiners.equal(_earlier_location_id_existing, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id_existing, lambda dtf: dtf.destination_id),
        )
        .penalize(HardMediumSoftScore.ONE_SOFT, _existing_fallback_minutes)
        .as_constraint("Travel time to existing assignment (fallback estimate)"),
        # Soft: an employee's drive from home to their first visit of the
        # day - "first" meaning no other same-employee-same-date visit has a
        # strictly earlier start time (ties both count as first).
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .if_not_exists(VisitAssignment, *first_visit_of_day_joiners)
        .join(
            DrivingTimeFact,
            *employee_leg_kind_joiners,
            Joiners.equal(lambda v: v.employee.id, lambda dtf: dtf.origin_id),
            Joiners.equal(lambda v: v.location_id, lambda dtf: dtf.destination_id),
        )
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda v, dtf: dtf.duration_minutes * _TIME_WEIGHT_PER_MINUTE,
        )
        .as_constraint("Employee home-to-visit travel time"),
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .if_not_exists(VisitAssignment, *first_visit_of_day_joiners)
        .if_not_exists(
            DrivingTimeFact,
            *employee_leg_kind_joiners,
            Joiners.equal(lambda v: v.employee.id, lambda dtf: dtf.origin_id),
            Joiners.equal(lambda v: v.location_id, lambda dtf: dtf.destination_id),
        )
        .penalize(HardMediumSoftScore.ONE_SOFT, _employee_fallback_minutes)
        .as_constraint("Employee home-to-visit travel time (fallback estimate)"),
    ]
