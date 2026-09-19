# Tasks

## 1. Solver domain model (`solver/app/domain.py`)

- [x] 1.1 Add `date: Annotated[date | None, PlanningVariable(value_range_provider_refs=["date_range"], allows_unassigned=True)]` to `VisitAssignment`, keeping `requested_date: date` as the fixed nominal-date fact (unchanged field, new meaning: preference anchor only, no longer used for constraint grouping)
- [x] 1.2 Add `interval_days: int | None`, `previous_visit_id: int | None`, `previous_actual_date: date | None` fields to `VisitAssignment`
- [x] 1.3 Add `candidate_dates: Annotated[list[date], ValueRangeProvider(id="date_range")]` to `Schedule`
- [x] 1.4 Rename `ExistingAssignmentFact.requested_date` to `date`, and verify (by reading `solve.py`'s `_build_schedule`, updated in task 4) that it's populated from the assignment's actual applied date - fixing the pre-existing bug described in design.md
- [x] 1.5 Verify the module still imports cleanly and every existing reference to the renamed/repurposed fields compiles (a deliberately broad check before touching `constraints.py`, since the next tasks depend on this file being correct)

## 2. Solver constraints - rewire existing joiners to the new `date` variable (`solver/app/constraints.py`)

- [x] 2.1 Update `_same_employee_same_date` and `_same_employee_same_date_cross` to join on `VisitAssignment.date` (and `ExistingAssignmentFact.date` per the task 1.4 rename) instead of `requested_date`
- [x] 2.2 Update `_visit_employee_id_same_date_schedule` (used by the working-hours and driving-time-before-first-visit constraints) the same way
- [x] 2.3 Update `_first_visit_of_day_joiners` the same way
- [x] 2.4 Verify by inspection that every constraint using these shared joiner lists (double-booking, both driving-time-gap variants, working-hours, "no resolved schedule", both home-to-first-visit variants) now correctly reflects each visit's *chosen* date rather than its nominal one - no constraint definition itself needs to change beyond the joiner update, since they were already written generically over "same date"

## 3. Solver constraints - the two new soft preferences (`solver/app/constraints.py`)

- [x] 3.1 Add a `_NOMINAL_DATE_WEIGHT_PER_DAY` constant (start conservative, e.g. 10x `_TIME_WEIGHT_PER_MINUTE`'s effective per-day equivalent - document the reasoning inline the way `_TIME_WEIGHT_PER_MINUTE` and `_unscheduled_priority_weight`'s constants already are) and a standalone `nominal_date_drift(constraint_factory)` soft constraint: for each scheduled visit, penalize `abs((visit.date - visit.requested_date).days) * _NOMINAL_DATE_WEIGHT_PER_DAY`
- [x] 3.2 Add a `_INTERVAL_SHORTFALL_WEIGHT_PER_DAY` constant, clearly weaker than 3.1's (document the ratio and that it's expected to need tuning, per design.md's Risks), and a standalone `interval_since_previous_occurrence_sibling(constraint_factory)` soft constraint: join `VisitAssignment` to `VisitAssignment` on `Joiners.equal(lambda v: v.previous_visit_id, lambda p: p.id)`, filter both scheduled and `v.interval_days is not None`, penalize `max(0, v.interval_days - (v.date - p.date).days) * _INTERVAL_SHORTFALL_WEIGHT_PER_DAY`
- [x] 3.3 Add `interval_since_previous_occurrence_existing(constraint_factory)`: same idea, joining `VisitAssignment` (filtered to `previous_actual_date is not None`) against that fixed date directly (no second entity join needed - it's a plain field on the visit fact), penalizing `max(0, v.interval_days - (v.date - v.previous_actual_date).days) * _INTERVAL_SHORTFALL_WEIGHT_PER_DAY`
- [x] 3.4 Wire both new constraints (3.1-3.3, three total) into `define_constraints`, as standalone functions matching the existing style (independently unit-testable via `ConstraintVerifier`, same as `unscheduled_visit`/the driving-time-gap functions)

## 4. Solver request/response schemas and solve wiring (`solver/app/schemas.py`, `solver/app/solve.py`)

- [x] 4.1 Add `interval_days: int | None`, `previous_visit_id: int | None`, `previous_actual_date: date | None` to `VisitIn`; add `candidate_dates: list[date]` to `OptimizeRequest`
- [x] 4.2 Add `date: date` to `ScheduledVisitOut`
- [x] 4.3 Update `_build_schedule` in `solve.py` to construct each `VisitAssignment` with the new fields (from the corresponding `VisitIn`), construct `Schedule.candidate_dates` from `request.candidate_dates`, and construct each `ExistingAssignmentFact` with its (corrected, per task 1.4) `date` field
- [x] 4.4 Update `solve_schedule`'s response-building loop to populate `ScheduledVisitOut.date` from each solved `VisitAssignment.date`
- [x] 4.5 Update `main.py`'s `_warm_up()` fixture (it constructs a minimal `OptimizeRequest`/`EmployeeIn`/`VisitIn` directly) to include the new required fields so the solver's own startup warm-up still succeeds

## 5. Backend payload building (`backend/app/solver_client.py`)

- [x] 5.1 Add a `_window_dates(days_ahead: int) -> set[date]` helper (today through today + min(days_ahead, MAX_DAYS_AHEAD) - 1 - the same window `_is_within_scheduling_window` already computes, factored out for reuse) and use it in place of the current visit-derived sparse `candidate_dates` wherever `_employee_day_schedule_payloads` is called, so every employee's schedule is sent for every date in the window, not just dates a visit happens to nominally fall on
- [x] 5.2 In `_load_run_data`, compute a `previous_occurrence_by_visit_id: dict[int, tuple[int | None, date | None, int | None]]` (previous_visit_id if that sibling is itself schedulable, previous_actual_date if the sibling has a locked assignment, interval_days) by grouping the already-loaded `all_visits` by `contract_line_id`, sorting by `requested_date`, and pairing each visit with its immediate predecessor in that ordering (see design.md's Decisions for the exact case logic); store it on `_RunData`
- [x] 5.3 Update `_visit_payload` to send `visit.requested_date.isoformat()` (raw, not floored to today) and the three new fields looked up from `previous_occurrence_by_visit_id`; leave `days_until_due` unchanged (still derived from `effective_schedule_date`, per design.md's Non-Goals)
- [x] 5.4 Update `_existing_assignment_payload` to send `"date": assignment.planned_start.date().isoformat()` under the renamed key (matching task 1.4/4.3), replacing the current `assignment.service_visit.requested_date` source - this is the pre-existing-bug fix described in design.md
- [x] 5.5 Update `_assemble_payload` (and its callers `build_optimize_payload`/`build_parallel_group_payloads`) to send `candidate_dates` (the full window from 5.1) in the payload, alongside the now-fuller `employee_day_schedules`
- [x] 5.6 Verify `_group_subset` (parallel execution mode) still passes each group's own subset of employees/visits/locked-assignments through unchanged, but with the same full-window `candidate_dates`/`employee_day_schedules` coverage as the single-mode path - the region split is orthogonal to date, so no group-specific date logic is needed

## 6. Backend response handling (`backend/app/main.py`)

- [x] 6.1 Update `propose_optimization`'s proposal-building loop to construct each `ProposedAssignmentOut`'s `planned_start`/`planned_end` from the solver's returned `date` (per scheduled item) instead of `effective_schedule_date(visit)`
- [x] 6.2 Verify by inspection that `apply_optimization` and `create_assignment` need no changes - they already just take whatever `planned_start` the caller (the applied proposal, built in 6.1) supplies

## 7. Unit tests

- [x] 7.1 Update the existing solver test fixtures that construct `VisitAssignment`/`ExistingAssignmentFact` directly (`solver/tests/test_driving_time_gap_constraints.py`, `test_solve_schedule_driving_time_gap.py`, `test_unscheduled_priority_weight.py`) to supply the new required fields (`date` set equal to `requested_date` for those tests, since they're not exercising the new behavior; `interval_days`/`previous_visit_id`/`previous_actual_date` as `None`), and confirm they still pass unmodified otherwise
- [x] 7.2 Add `solver/tests/test_nominal_date_drift_constraint.py`: verify the penalty scales with `abs(date - requested_date)` in days, verify zero penalty when they're equal, using `ConstraintVerifier`
- [x] 7.3 Add `solver/tests/test_interval_since_previous_occurrence_constraint.py`: both the sibling-join and existing-assignment-join variants - verify a placement respecting the interval gets no penalty, verify a shortfall gets a penalty proportional to the shortfall, verify a visit with no previous occurrence (`interval_days=None`) never triggers either constraint
- [x] 7.4 Add a `solver/tests` end-to-end test (matching `test_solve_schedule_driving_time_gap.py`'s style of calling `solve_schedule` directly) reproducing the worked example from design.md: a biweekly contract line's visit 1 already locked (existing assignment) on a date later than its own nominal date, visit 2's nominal date has capacity - assert `solve_schedule` places visit 2 on its own nominal date, not pushed later to satisfy the interval
- [x] 7.5 Add a backend unit test (no DB, no HTTP, matching `test_plan_from_floor.py`'s style) for the previous-occurrence/interval computation logic from task 5.2, using lightweight stand-in objects (matching `test_solver_partitioning.py`'s pattern): a middle occurrence with both a schedulable predecessor and successor, a first occurrence (no predecessor), and a predecessor with a locked assignment

## 8. Manual verification

- [x] 8.1 Reproduce the worked example live against a real (or realistic test) dataset: a biweekly contract line, its first visit manually delayed a few days past its nominal date (via a locked/applied assignment), confirm a fresh proposal run places the second visit on its own nominal date when that date has capacity
- [x] 8.2 Same setup, but with the second visit's nominal date deliberately made infeasible (e.g. no employee capacity that day); confirm the proposal places it close to (previous occurrence's actual date + the contract's interval) rather than immediately adjacent to the previous occurrence
- [x] 8.3 Run the full existing solver test suite (`solver/tests/`) and confirm every pre-existing test still passes unmodified in behavior (only the fixture updates from 7.1), confirming the hard constraints (skills, region, working hours, double-booking, driving-time gaps) are unaffected by the date-joiner rewiring
- [x] 8.4 Run a multi-day proposal (`days_ahead` >= 3) against real dev data where today has more ready visits than capacity and later days are comparatively empty; confirm visits that don't fit today are now proposed on a later day within the window, addressing the original report this change exists to fix
- [x] 8.5 Run the same multi-day proposal with `execution_mode: "parallel"`; confirm it still produces a valid merged proposal (no employee double-booked across groups, per the existing parallel-mode guarantee) with the new date freedom in play within each group
- [x] 8.6 Run a proposal with a `plan_from_time` later than 08:00; confirm the floor still only affects today's placements and does not affect the employee's availability on other days in the window, now that `employee_day_schedules` covers the full window per employee
- [x] 8.7 Confirm solve time for a realistic `days_ahead` (e.g. 5-7) and visit volume stays within an acceptable range for the configured `time_limit_seconds` - if solve quality or time visibly degrades relative to before this change, report it rather than treating it as an acceptable silent regression (see design.md's Risks). Found a real regression at realistic scale (~150 visits); reported it, then shipped `_default_time_limit_seconds` (scales the default time budget with window size, capped at 90s) as a partial mitigation - see design.md's Risks for the measured before/after and the residual limitation deferred to a follow-up change.
