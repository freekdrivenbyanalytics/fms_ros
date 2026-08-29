## Why

Assigning visits today is entirely manual: a planner picks an employee and a start time for one unassigned visit at a time, with no help finding a schedule that respects everyone's working hours, skills, and regions while minimizing how much employees have to travel between visits. As the number of unassigned visits grows, manually finding a good schedule becomes impractical. A route-optimization service that proposes a full schedule for all unassigned visits — which a planner reviews and applies — turns this into a one-click starting point instead of a fully manual chore.

## What Changes

- Stand up a new, standalone solver service (its own process, not embedded in the existing backend) that uses Timefold Solver to compute an optimized schedule: which employee is assigned to which currently-unassigned visit, and at what time.
- The solver's plan for each visit keeps that visit's date fixed to its own `requested_date` (it schedules time-of-day and employee, not which day) and, within each employee's day, sequences that employee's visits to minimize total travel distance between them (using existing employee/customer-location latitude/longitude) — a genuine route-optimization objective, not just constraint matching.
- Hard constraints the solver must satisfy: an assigned employee has every skill the visit's contract requires; the employee is scoped to the visit's region; the visit's planned time window falls within the employee's working hours; the employee has no time overlap with any other visit already assigned to them (existing assignments) or with any other visit newly proposed to them in the same run.
- One optimization run considers every currently unassigned service visit, across all dates, together with every employee's existing assignments (which the solver treats as fixed and never moves).
- Add a backend endpoint that gathers the current employees/unassigned-visits/assignments, calls the solver service, and returns the proposed schedule — without creating any real `Assignment` rows yet.
- Add a backend endpoint that accepts a previously returned proposal and creates real `Assignment` rows for it, reusing the existing single-assignment validation (rejecting a visit that became assigned in the meantime).
- Add a new "Optimize" view to the Planning frontend (a third option alongside Manual Assignment and Day Planning): a button to run the optimizer, a review table showing the full proposed schedule (visit → employee → proposed time), and an "Apply All" action that commits the entire reviewed proposal at once. No partial/selective apply in this first version — reviewing and applying is all-or-nothing (revisit if that proves too coarse in practice).
- No changes to the existing manual-assignment flow, its data model, or its endpoints — this adds a new way to create assignments, in addition to the existing manual one.

## Capabilities

### New Capabilities
- `route-optimization`: Computing a proposed employee/visit schedule via an external solver service, reviewing it, and applying it to create real assignments.

## Impact

- **Affected code**: A new top-level `solver/` service (its own Python project, dependencies, and process) implementing the Timefold Solver model and exposing an HTTP API; `backend/app/config.py` (solver service base URL), a new `backend/app/solver_client.py`, new endpoints in `backend/app/main.py`; a new `frontend/src/OptimizeView.tsx` (or similar) plus wiring into `frontend/src/App.tsx`'s view switch and `frontend/src/api.ts`.
- **Affected systems**: Introduces a new service to run locally (or deploy) alongside the backend and frontend — a third process for local dev. No database schema changes are anticipated (proposals are ephemeral, only applying them writes `Assignment` rows via the existing table).
- **Dependencies**: The `timefold` Python solver library (Apache-2 licensed community edition) in the new solver service — confirmed during implementation to be a Java library wrapped via JPype, so it requires a JVM at runtime; `jdk4py` (a pip-installable JDK) is added so this stays self-contained without a system-wide Java install. An HTTP client already available in the backend (`httpx`, added for the Tripletex integration) for calling the solver service.
