# Proposal

## Why

Two rough edges surfaced from real use of the Optimize and Day Planning pages: the day-planning route map goes from nothing to fully drawn with no indication it's loading, and its routes have no legend, so a planner can't tell which color belongs to which employee without clicking each route individually. Separately, a schedule run always proposes visits starting from each employee's normal working-hours start (e.g. 08:00), even when it's already mid-morning and some of that time is no longer realistic to plan into — there's no way to tell the optimizer "don't propose anything before now."

(A fourth report — "optimize for two days ahead only proposes one day" — was investigated live against the current dev data: today has 129 ready-to-schedule visits, tomorrow has 1, because the demo-data refresh script collapses visit dates near today rather than spreading them out. The `days_ahead` scheduling-window logic itself is confirmed correct (it produces a real N-day window). Not a bug in this system; excluded from this change.)

## What Changes

- The day-planning route map shows a loading indicator while its routes are being fetched, instead of an empty space.
- The day-planning route map shows a legend mapping each employee's route color to their name.
- A proposed schedule run gains a "plan from" time parameter (default 08:00), applied only to *today's* portion of the run: no visit is proposed to start earlier than this time today, regardless of an employee's normal working-hours start. Days after today are unaffected — each starts at the employee's normal working-hours start as today, since a future day hasn't partially elapsed yet. Exposed as a time input on the Optimize page's existing controls row.

## Capabilities

### Modified Capabilities
- `day-planning`: adds a loading state for the route map, and a legend requirement for route colors.
- `route-optimization`: adds a configurable "plan from" time floor applied to today's portion of a run.

## Impact

- **Affected code**: `frontend/src/components/DayPlanningView.tsx`, `frontend/src/components/DayRouteMap.tsx` (loading state, legend); `backend/app/schemas.py` (`OptimizeRunOptions`), `backend/app/solver_client.py` (`_employee_day_schedule_payloads` / today's start-minutes floor), `frontend/src/components/OptimizeView.tsx`, `frontend/src/api.ts`, `frontend/src/types.ts` (plan-from-time control and plumbing).
- **Affected systems**: none beyond the existing backend/solver/frontend split — no new external dependency.
- **Dependencies**: none. Independent of the currently-implemented `add-parallel-region-solving` change's `execution_mode` parameter — this adds a sibling parameter to the same `OptimizeRunOptions`/Optimize-page controls.
