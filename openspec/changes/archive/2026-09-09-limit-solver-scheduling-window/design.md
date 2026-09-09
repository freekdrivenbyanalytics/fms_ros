## Context

`build_optimize_payload` (`backend/app/solver_client.py`) already computes `effective_schedule_date(v)` per visit and already splits visits into `schedulable_visits` (candidates) vs. `locked_assignments` (fixed facts: pinned or already started). It has no date-range filter today — every schedulable visit, regardless of date, becomes a candidate; `candidate_dates` is simply the set of all their effective dates, used only to know which `EmployeeDaySchedule`s to fetch. See proposal.md - Why for the performance motivation.

## Goals / Non-Goals

**Goals:**
- Shrink the solver's candidate set to only today's and tomorrow's visits.
- Keep the exclusion mechanism consistent with the existing ungeocoded/regionless exclusions (added to `excluded_visit_ids`, reported via `unscheduled_visit_ids`).

**Non-Goals:**
- Making the window configurable (e.g., a setting for "N days ahead"). The user asked specifically for today and tomorrow; a config knob is unrequested complexity until there's a reason to vary it.
- Filtering `locked_assignments` (pinned/started assignments) by date. They're already-fixed facts sent to the solver so it doesn't double-book an employee; leaving in ones outside the window is harmless (see Decisions) and removing them is a pure micro-optimization that isn't needed to satisfy the spec.

## Decisions

- **Filter at candidate-selection time, before `ready_visits`/`candidate_dates` are computed.** Add the date-window check alongside the existing `_is_ready_to_schedule` filter, so out-of-window visits flow into `excluded_visit_ids` the same way ungeocoded/regionless ones already do — no new response shape, no change to how the caller (Planning app) distinguishes "scheduled" from "unscheduled."
- **Leave `locked_assignments` unfiltered.** They're sent as fixed facts purely so the solver's overlap/hard-constraint checks see an employee's existing commitments; an employee's day-N+5 pinned visit can't overlap a day-0/day-1 candidate, so including it costs a little payload size but changes no outcome. Filtering it out is a valid future micro-optimization, not a behavior requirement — left out to keep this change minimal and easy to verify.
- **"Effective schedule date," not "requested date," is what's windowed.** Reusing the existing `effective_schedule_date` helper (already reschedules past-due visits to today) means a visit requested last week still gets picked up today rather than being permanently stranded — consistent with the existing "Proposed schedule keeps each visit's effective schedule date" requirement.

## Risks / Trade-offs

- [A visit 3+ days out never gets a preview proposal, so a planner can't look ahead] → Accepted trade-off per the user's explicit request; the existing `/service-visits` list still shows every future visit's requested date, just without a proposed employee/time until it's within the window.
