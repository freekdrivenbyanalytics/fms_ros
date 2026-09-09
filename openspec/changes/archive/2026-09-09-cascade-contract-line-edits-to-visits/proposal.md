## Why

Editing a contract line today only changes the line's own fields — its generated service visits are left exactly as they were, even when the edit changes what those visits should be (different products, a different cadence, a different end date). A planner who updates a line has to remember to separately clean up and regenerate its visits by hand. The business wants editing a contract line to automatically keep its not-yet-started visits in sync with the line's current terms, and wants a friendlier way to mark a line as open-ended than leaving the end-date field blank.

## What Changes

- Updating a contract line (`PATCH /contract-lines/{id}`) now removes every one of that line's service visits that has not yet started — unassigned ones, and assigned-but-not-yet-started ones, including pinned ones — and regenerates the line's future visits from its current (just-saved) products, duration, interval, and end date. Visits with a started assignment (per the existing `assignments` capability definition — planned_start already passed) are left untouched; this only ever affects the future.
- Regeneration picks up where the line's real history left off: the anchor is the requested_date of the line's most recent visit with a started assignment, or the line's own `start_date` if none of its visits have started yet. This avoids the naive bug of regenerating from "today" and silently skipping or duplicating occurrences. When nothing has started and that `start_date` is in the past, the first regenerated visit is dated today rather than the stale original date — but every visit after that still lands on the cadence the original `start_date` implies, so the schedule's pattern (e.g. "every other Tuesday") isn't reset just because it's being regenerated late.
- The Admin Portal's contract-line form gains an "No end date" checkbox. Checking it greys out the end-date field and displays `31.12.2099` in it as a visual placeholder; the checkbox conveys "open-ended," not the literal date — the field the form actually submits is `end_date: null`, exactly as it works today, so the existing open-ended behavior (90-day rolling horizon, "Extend recurring visits") is unaffected.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `service-visits`: adds a requirement that updating a contract line regenerates its not-yet-started visits from the line's current terms, anchored at its last-started visit (or start_date if none).
- `contracts`: "Create, update, and soft-delete a contract line" now references the service-visits regeneration rule, the way visit *creation* already does.
- `admin-portal`: adds the "No end date" checkbox to the contract-line form.

## Impact

- `backend/app/main.py`: `update_contract_line` gains a regeneration step; new helper to find not-yet-started visits for a line and delete them (reusing the existing "started = planned_start has passed" definition already used for the assignment auto-lock), and to compute the new occurrence dates (reusing `generate_occurrence_dates`/`extend_occurrence_dates` from `visit_generation.py` — no new date-math needed).
- `frontend/src/admin-portal/ContractsView.tsx`: `ContractLineForm` gains the "No end date" checkbox, wired to disable/grey the end-date input and display `31.12.2099`, while still submitting `end_date: null`.
- **Deliberate exception to existing pin protection**: unlike a schedule run (which never touches a pinned assignment) or manual unassign (a single explicit user action), this cascade removes not-yet-started pinned assignments as a side effect of editing the contract line they belong to. Flagged here since it's the one place this change knowingly overrides an existing invariant.
