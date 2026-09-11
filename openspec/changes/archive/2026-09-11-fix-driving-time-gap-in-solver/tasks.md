## 1. Proposed-proposed driving-time gap

- [x] 1.1 Add a hard constraint that filters same-employee-same-date `VisitAssignment` pairs (ordered by `start_minutes`) where `later.start_minutes - earlier.end_minutes()` is less than the matched `DrivingTimeFact.duration_minutes`, penalizing `HardMediumSoftScore.ONE_HARD`
- [x] 1.2 Add the `if_not_exists(DrivingTimeFact, ...)` fallback variant using `_pair_fallback_minutes`, same ordering and penalty

## 2. Proposed-existing driving-time gap

- [x] 2.1 Add a hard constraint for `VisitAssignment` × `ExistingAssignmentFact` pairs, ordered by start time in both directions (existing-before-proposed and proposed-before-existing), where the gap is less than the matched `DrivingTimeFact.duration_minutes`, penalizing `HardMediumSoftScore.ONE_HARD`
- [x] 2.2 Add the `if_not_exists(DrivingTimeFact, ...)` fallback variant using `_existing_fallback_minutes`

## 3. Employee home-to-first-visit driving-time gap

- [x] 3.1 Add a hard constraint, using the existing `first_visit_of_day_joiners` pattern, that filters an employee's first visit of the day where `visit.start_minutes - schedule.start_minutes` is less than the matched `DrivingTimeFact.duration_minutes`, penalizing `HardMediumSoftScore.ONE_HARD`
- [x] 3.2 Add the `if_not_exists(DrivingTimeFact, ...)` fallback variant using `_employee_fallback_minutes`

## 4. Verify against existing behavior

- [x] 4.1 Add constraint-level tests (using Timefold's `ConstraintVerifier`, bundled in `timefold.solver.test`) for each of the six new constraints: one case that should be penalized (gap smaller than driving time) and one that should not (gap exactly equal to or larger than driving time)
- [x] 4.2 Run a full `solve_schedule` against a small fixture with two same-employee visits at different locations and confirm the proposed gap between them is now always >= the driving time (or one of them is left unscheduled)
- [x] 4.3 Check `backend/app/seed.py` and `backend/app/reset_demo_data.py` (the actual demo/seed data scripts) for any zero-gap back-to-back visit assumptions the new hard constraints would newly reject - neither creates `Assignment` rows with hardcoded timing (seed.py creates no assignments at all; reset_demo_data.py only deletes them), so there's nothing to adjust

## 5. Manual verification

- [x] 5.1 Start the backend + solver locally, run "Run Optimization" from the admin portal on a dataset with tight visit windows, and confirm every proposed pair of same-day visits for an employee leaves at least the driving-time gap between them - verified against the already-running dev stack (Docker Postgres, backend, solver) by calling `POST /optimize/propose` directly (the same endpoint the admin portal's "Run Optimization" button calls) against the live seeded dataset (3 employees, 1050 visits), then cross-checking every consecutive-visit gap and every home-to-first-visit gap in the 12-visit proposal against the real `driving_times` table / Haversine fallback. All gaps satisfy the new hard constraints, including one tight case (45-minute gap against a 44-minute required drive for employee 2), confirming the constraint is actually binding in practice
