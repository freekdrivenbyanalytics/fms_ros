# Proposal

## Why

A schedule run currently pins every visit's date to a single fixed value before the solver ever runs (`effective_schedule_date`: the visit's own `requested_date`, or today if that's already passed). The solver only ever chooses *employee* and *time of day* for that one fixed date. When a day has more ready visits than the workforce can cover, the excess simply goes unscheduled — even when `days_ahead` spans several days and later days have free capacity — because nothing in the solver is allowed to move a visit to a different day.

Investigated live against the current dev data: on a typical day, most visits share the same contract cadence and land on the same one or two dates, while the following days are nearly empty. A 2-day-ahead run therefore behaves like a 1-day run in practice.

Two real constraints shape the fix, from live discussion with the business owner: visits **shouldn't** simply be allowed to drift to whatever day has room — pushed too early relative to the contract's cadence, two consecutive visits for the same contract line can end up clustered back-to-back at a period boundary (one pushed toward the end of its period, the next pulled to the start of the next); and the interval must stay anchored to the **contract's own nominal cadence**, not to wherever a previous visit actually happened to land — otherwise a single early delay compounds forward indefinitely and the contract quietly loses serviced visits (and the revenue tied to them) over time.

## What Changes

- The solver gains a second per-visit planning decision: which *day* within the run's scheduling window a visit lands on, alongside the existing employee/time-of-day decisions. This lets Timefold jointly reason across the whole window — e.g. moving a visit that fits equally well tomorrow to free up today's capacity for a visit that can only go today — something no day-by-day approach can do, since each day's plan would already be locked before the next is considered.
- Two new soft preferences guide that choice, weighted so the solver only drifts a visit's date when it has to:
  - Prefer landing on the visit's own nominal (contract-cadence) date. Drifting earlier or later than that is possible but incurs a growing penalty the further it drifts.
  - Prefer keeping at least the contract's requested interval since the *previous* occurrence of the same contract line's *nominal* cadence date — not the previous visit's actual date, so a single delay doesn't licence every subsequent occurrence to drift further and further from the contract schedule.
- No visit can ever be proposed for a date before today, or outside the run's chosen scheduling window — matches today's behavior for the window's outer bounds; only the door for a *later* placement within that same window is newly open.
- Along the way, a bug this redesign is directly entangled with gets fixed: an already-scheduled visit's "date" fact fed to the solver today is sourced from the *visit's* nominal `requested_date`, not the *assignment's* actual `planned_start` date — meaning a visit that was rescheduled after being overdue could silently fail to same-day-match against its own now-neighboring visits for driving-time-gap and double-booking checks.

## Capabilities

### Modified Capabilities
- `route-optimization`: a proposed schedule run's date choice becomes a solver decision (bounded to the run's scheduling window) rather than a fixed input; adds the two new soft preferences (closeness to nominal date, minimum interval since the previous nominal occurrence) governing that choice.

## Impact

- **Affected code**:
  - `solver/app/domain.py`: `VisitAssignment` gains a `date` planning variable (value range: every date in the run's scheduling window) and new fact fields (`interval_days`, `previous_visit_id`, `previous_actual_date`); `Schedule` gains the `date_range` value-range provider. `ExistingAssignmentFact`'s date field is corrected to source from the assignment's actual date (see the bug above).
  - `solver/app/constraints.py`: every constraint currently grouping by `visit.requested_date` (double-booking, driving-time gaps, working-hours/schedule lookups, first-visit-of-day) switches to the new `visit.date`. Two new soft constraints added for the preferences above.
  - `backend/app/solver_client.py`: `_visit_payload` sends the visit's true nominal `requested_date` (no longer floored to today) plus the new interval/previous-occurrence fields, computed from already-loaded sibling `ServiceVisit` rows for the same contract line (no new queries); `_existing_assignment_payload`'s date field is corrected per the bug fix above. `employee_day_schedules` must now cover every date in the run's window per employee (not just the dates visits happen to nominally fall on), since the solver can place a visit on any day in that window.
  - `route-optimization` spec: requirement text for "keeps each visit's effective schedule date" is replaced by the new date-is-a-solver-decision behavior, bounded to the scheduling window.
- **Affected systems**: none beyond the existing backend/solver split — no new external dependency.
- **Non-Goals** (see design.md): `days_until_due`/priority-tier weighting for unscheduled visits is unchanged — this change does not touch that already-carefully-tuned scoring; the `parallel` execution mode's region-grouping is unaffected (it groups by region/employee, an orthogonal axis to date).
- **Dependencies**: none on other in-flight changes. Builds on the currently-shipped `execution_mode`/`plan_from_time` parameters (both unaffected by this change) from recent prior changes.
