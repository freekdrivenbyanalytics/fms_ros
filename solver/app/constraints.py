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
# distance to an estimated raw-minutes figure, comparable to a real
# driving-time entry's duration_minutes. Callers that need a soft-score
# penalty (rather than a raw-minutes feasibility threshold) multiply by
# _TIME_WEIGHT_PER_MINUTE themselves, same as they do with a matched
# DrivingTimeFact's duration_minutes.
_ASSUMED_AVERAGE_SPEED_KMH = 40

_CUSTOMER_LOCATION = "customer_location"
_EMPLOYEE = "employee"

# Weighting for the "Unscheduled visit" medium penalty: priority strictly
# dominates urgency, and a single higher-priority (numerically lower)
# unscheduled visit must always outweigh ANY NUMBER of lower-priority ones
# left unscheduled instead - not just a handful. Because Timefold *sums*
# constraint match weights rather than taking a max, a flat per-tier
# multiplier (fixed or scaled to visit count) can never guarantee that: a
# lower tier's own per-visit weight is already the same order of magnitude
# as the gap, so summing just 2-3 of them overtakes one higher-tier visit
# regardless of the constant chosen. The only guarantee that survives
# summation is a *nested* one, where each tier's constant exceeds the
# maximum possible sum of every visit at the tier(s) below it - see
# _unscheduled_priority_weight.
_URGENCY_CAP = 14
# Strict upper bound on the urgency term (URGENCY_CAP - days_until_due,
# which is in [1, URGENCY_CAP] for any in-window visit).
_URGENCY_UPPER_BOUND = _URGENCY_CAP + 1


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def _haversine_fallback_minutes(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    km = _haversine_km(lat1, lon1, lat2, lon2)
    return int(round(km / _ASSUMED_AVERAGE_SPEED_KMH * 60))


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


def _gap_minutes(a: VisitAssignment, b: VisitAssignment) -> int:
    """Minutes between the earlier visit's end and the later visit's start,
    whichever of a/b that turns out to be - negative if they overlap."""
    if a.start_minutes <= b.start_minutes:
        return b.start_minutes - a.end_minutes()
    return a.start_minutes - b.end_minutes()


def _earlier_location_id_existing(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    return v.location_id if v.start_minutes <= e.start_minutes else e.location_id


def _later_location_id_existing(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    return e.location_id if v.start_minutes <= e.start_minutes else v.location_id


def _existing_fallback_minutes(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    return _haversine_fallback_minutes(v.latitude, v.longitude, e.latitude, e.longitude)


def _gap_minutes_existing(v: VisitAssignment, e: ExistingAssignmentFact) -> int:
    """Same as _gap_minutes, for a proposed visit paired with an existing
    fixed assignment."""
    if v.start_minutes <= e.start_minutes:
        return e.start_minutes - v.end_minutes()
    return v.start_minutes - e.end_minutes


def _employee_fallback_minutes(v: VisitAssignment) -> int:
    return _haversine_fallback_minutes(
        v.employee.latitude, v.employee.longitude, v.latitude, v.longitude
    )


# Shared joiner lists, at module scope so both define_constraints and the
# standalone constraint functions below (each independently unit-testable
# via ConstraintVerifier.verify_that) can use them.
_same_employee_same_date = [
    Joiners.equal(lambda v: v.employee),
    Joiners.equal(lambda v: v.requested_date),
]
_same_employee_same_date_cross = [
    Joiners.equal(lambda v: v.employee, lambda e: e.employee),
    Joiners.equal(lambda v: v.requested_date, lambda e: e.requested_date),
]
_visit_employee_id_same_date_schedule = [
    Joiners.equal(lambda v: v.employee.id, lambda s: s.employee_id),
    Joiners.equal(lambda v: v.requested_date, lambda s: s.date),
]
# A visit's own driving-time leg to another location is always customer
# location <-> customer location; an employee's home leg is always
# employee -> customer location. These constant-valued joiners guard
# against origin_id/destination_id collisions across the two independent
# id spaces (a customer_location id and an employee id can coincide).
_pair_kind_joiners = [
    Joiners.equal(lambda a, b: _CUSTOMER_LOCATION, lambda dtf: dtf.origin_kind),
    Joiners.equal(lambda a, b: _CUSTOMER_LOCATION, lambda dtf: dtf.destination_kind),
]
_employee_leg_kind_joiners = [
    Joiners.equal(lambda v: _EMPLOYEE, lambda dtf: dtf.origin_kind),
    Joiners.equal(lambda v: _CUSTOMER_LOCATION, lambda dtf: dtf.destination_kind),
]
_first_visit_of_day_joiners = [
    Joiners.equal(lambda v: v.employee, lambda o: o.employee),
    Joiners.equal(lambda v: v.requested_date, lambda o: o.requested_date),
    Joiners.greater_than(lambda v: v.start_minutes, lambda o: o.start_minutes),
]
# Same shape as _employee_leg_kind_joiners, but for use after a stream has
# already been joined with EmployeeDaySchedule (a (visit, schedule) tuple),
# where the left-hand mapper needs to accept both stream elements.
_employee_leg_kind_joiners_with_schedule = [
    Joiners.equal(lambda v, s: _EMPLOYEE, lambda dtf: dtf.origin_kind),
    Joiners.equal(lambda v, s: _CUSTOMER_LOCATION, lambda dtf: dtf.destination_kind),
    Joiners.equal(lambda v, s: v.employee.id, lambda dtf: dtf.origin_id),
    Joiners.equal(lambda v, s: v.location_id, lambda dtf: dtf.destination_id),
]


def _unscheduled_priority_weight(visit: VisitAssignment) -> int:
    """Nested-scale weight: priority 3's weight is just its urgency term;
    priority 2's tier constant (T2) exceeds N visits' worth of priority 3's
    maximum weight; priority 1's tier constant (T1) exceeds N visits' worth
    of priority 2's maximum weight (which already dominates priority 3). N
    is this run's total visit count - an absolute upper bound on how many
    visits could ever be simultaneously unscheduled - so the dominance holds
    regardless of how many lower-priority visits compete with a higher one."""
    n = visit.total_visit_count
    urgency = _URGENCY_CAP - visit.days_until_due

    if visit.priority >= 3:
        return urgency

    tier_2_constant = n * _URGENCY_UPPER_BOUND + 1
    if visit.priority == 2:
        return tier_2_constant + urgency

    tier_1_constant = n * (tier_2_constant + _URGENCY_UPPER_BOUND) + 1
    return tier_1_constant + urgency


def unscheduled_visit(constraint_factory: ConstraintFactory) -> Constraint:
    """Medium: prefer scheduling every visit over leaving it unassigned,
    weighted so a higher-priority (numerically lower) unscheduled visit
    always outweighs any realistic number of lower-priority ones, and,
    within the same priority, a sooner-due visit outweighs a later one -
    see _unscheduled_priority_weight."""
    return (
        constraint_factory.for_each_including_unassigned(VisitAssignment)
        .filter(_is_unassigned)
        .penalize(HardMediumSoftScore.ONE_MEDIUM, _unscheduled_priority_weight)
        .as_constraint("Unscheduled visit")
    )


def driving_time_gap_between_proposed_visits(constraint_factory: ConstraintFactory) -> Constraint:
    """Hard: leave enough time to actually drive between two same-day
    proposed visits, using a computed driving-time entry when one covers
    the leg. See _gap_minutes for how the gap is computed regardless of
    which of the pair the constraint stream hands over first."""
    return (
        constraint_factory.for_each_unique_pair(VisitAssignment, *_same_employee_same_date)
        .filter(_both_scheduled)
        .join(
            DrivingTimeFact,
            *_pair_kind_joiners,
            Joiners.equal(_earlier_location_id, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id, lambda dtf: dtf.destination_id),
        )
        .filter(lambda a, b, dtf: _gap_minutes(a, b) < dtf.duration_minutes)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Not enough time to drive between proposed visits")
    )


def driving_time_gap_between_proposed_visits_fallback(
    constraint_factory: ConstraintFactory,
) -> Constraint:
    """Hard: same as driving_time_gap_between_proposed_visits, using the
    Haversine-derived fallback when no DrivingTimeFact covers the leg."""
    return (
        constraint_factory.for_each_unique_pair(VisitAssignment, *_same_employee_same_date)
        .filter(_both_scheduled)
        .if_not_exists(
            DrivingTimeFact,
            *_pair_kind_joiners,
            Joiners.equal(_earlier_location_id, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id, lambda dtf: dtf.destination_id),
        )
        .filter(lambda a, b: _gap_minutes(a, b) < _pair_fallback_minutes(a, b))
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Not enough time to drive between proposed visits (fallback estimate)")
    )


def driving_time_gap_to_existing_assignment(constraint_factory: ConstraintFactory) -> Constraint:
    """Hard: same as driving_time_gap_between_proposed_visits, but between a
    proposed visit and an existing fixed assignment."""
    return (
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(ExistingAssignmentFact, *_same_employee_same_date_cross)
        .join(
            DrivingTimeFact,
            *_pair_kind_joiners,
            Joiners.equal(_earlier_location_id_existing, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id_existing, lambda dtf: dtf.destination_id),
        )
        .filter(lambda v, e, dtf: _gap_minutes_existing(v, e) < dtf.duration_minutes)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Not enough time to drive to existing assignment")
    )


def driving_time_gap_to_existing_assignment_fallback(
    constraint_factory: ConstraintFactory,
) -> Constraint:
    """Hard: same as driving_time_gap_to_existing_assignment, using the
    Haversine-derived fallback when no DrivingTimeFact covers the leg."""
    return (
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .join(ExistingAssignmentFact, *_same_employee_same_date_cross)
        .if_not_exists(
            DrivingTimeFact,
            *_pair_kind_joiners,
            Joiners.equal(_earlier_location_id_existing, lambda dtf: dtf.origin_id),
            Joiners.equal(_later_location_id_existing, lambda dtf: dtf.destination_id),
        )
        .filter(lambda v, e: _gap_minutes_existing(v, e) < _existing_fallback_minutes(v, e))
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Not enough time to drive to existing assignment (fallback estimate)")
    )


def driving_time_gap_before_first_visit(constraint_factory: ConstraintFactory) -> Constraint:
    """Hard: leave enough time to drive from an employee's home to their
    first visit of the day, starting from their working-hours start. Needs
    the day's resolved start time, so this joins EmployeeDaySchedule -
    unlike the soft "Employee home-to-visit travel time" constraint, which
    only scores the leg and doesn't care when the workday starts."""
    return (
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .if_not_exists(VisitAssignment, *_first_visit_of_day_joiners)
        .join(EmployeeDaySchedule, *_visit_employee_id_same_date_schedule)
        .join(DrivingTimeFact, *_employee_leg_kind_joiners_with_schedule)
        .filter(lambda v, s, dtf: v.start_minutes - s.start_minutes < dtf.duration_minutes)
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Not enough time to drive from home to first visit")
    )


def driving_time_gap_before_first_visit_fallback(
    constraint_factory: ConstraintFactory,
) -> Constraint:
    """Hard: same as driving_time_gap_before_first_visit, using the
    Haversine-derived fallback when no DrivingTimeFact covers the leg."""
    return (
        constraint_factory.for_each(VisitAssignment)
        .filter(_is_scheduled)
        .if_not_exists(VisitAssignment, *_first_visit_of_day_joiners)
        .join(EmployeeDaySchedule, *_visit_employee_id_same_date_schedule)
        .if_not_exists(DrivingTimeFact, *_employee_leg_kind_joiners_with_schedule)
        .filter(lambda v, s: v.start_minutes - s.start_minutes < _employee_fallback_minutes(v))
        .penalize(HardMediumSoftScore.ONE_HARD)
        .as_constraint("Not enough time to drive from home to first visit (fallback estimate)")
    )


@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory) -> list[Constraint]:
    same_employee_same_date = _same_employee_same_date
    same_employee_same_date_cross = _same_employee_same_date_cross
    visit_employee_id_same_date_schedule = _visit_employee_id_same_date_schedule
    pair_kind_joiners = _pair_kind_joiners
    employee_leg_kind_joiners = _employee_leg_kind_joiners
    first_visit_of_day_joiners = _first_visit_of_day_joiners

    return [
        # Medium: defined as a standalone function above so it's
        # independently unit-testable via ConstraintVerifier.
        unscheduled_visit(constraint_factory),
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
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda a, b: _pair_fallback_minutes(a, b) * _TIME_WEIGHT_PER_MINUTE,
        )
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
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda v, e: _existing_fallback_minutes(v, e) * _TIME_WEIGHT_PER_MINUTE,
        )
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
        .penalize(
            HardMediumSoftScore.ONE_SOFT,
            lambda v: _employee_fallback_minutes(v) * _TIME_WEIGHT_PER_MINUTE,
        )
        .as_constraint("Employee home-to-visit travel time (fallback estimate)"),
        # Hard: leaving less than the driving time between two same-day
        # visits (or before the first visit) is infeasible, not just
        # undesirable. Defined as standalone functions above so each is
        # independently unit-testable via ConstraintVerifier.
        driving_time_gap_between_proposed_visits(constraint_factory),
        driving_time_gap_between_proposed_visits_fallback(constraint_factory),
        driving_time_gap_to_existing_assignment(constraint_factory),
        driving_time_gap_to_existing_assignment_fallback(constraint_factory),
        driving_time_gap_before_first_visit(constraint_factory),
        driving_time_gap_before_first_visit_fallback(constraint_factory),
    ]
