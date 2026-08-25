## Why

The only existing view is the manual-assignment page (`frontend/src/App.tsx`), which lists employees and visits as cards but never shows *when* each employee is busy across a day. A planner reviewing how a day's work is laid out has to mentally reconstruct the schedule from scattered planned_start/planned_end times. A read-only, per-employee timeline for a chosen day makes a day's plan reviewable at a glance.

## What Changes

- Add a new "Day Planning" page, separate from the existing manual-assignment page, reachable via in-app navigation (no routing library is present today; this adds a simple client-side view switch, not URL routing).
- The page shows a single combined timeline chart covering all employees together — one row per employee within that one chart, not a separate chart per employee — with a horizontal block for each assignment spanning planned_start to planned_end, labeled with the visit's customer name.
- Each timeline block expands (reusing the existing `InfoBox` pattern already used for employee/visit cards) to show the assignment's full service visit detail: customer, address, region, and required skills.
- Each employee row's label shows the skills that employee possesses, matching the skill-pill styling already used in `EmployeeList`.
- A date control (prev/next plus a picker) selects which day's assignments are shown; the page defaults to today.
- The view is read-only: no drag, resize, or click-to-edit an assignment — expanding a block for detail is not an edit action; assignments can still only be created from the existing manual-assignment page.
- No backend changes: the page reuses the existing `GET /assignments` and `GET /employees` endpoints and filters assignments to the selected day's `planned_start` on the client.

## Capabilities

### New Capabilities
- `day-planning`: A read-only, per-employee timeline view of a selected day's assignments, with date navigation.

### Modified Capabilities
None — the existing `assignments` capability (data model, manual assignment, and the manual-assignment page) is unchanged; this change only adds a new, separate read-only view over the same data.

## Impact

- **Affected code**: `frontend/src/` — new page component(s) and a top-level view switch in `App.tsx`; no changes to `frontend/src/api.ts` request shapes (existing `listAssignments`/`listEmployees` are reused).
- **Affected systems**: Frontend only. No backend, API, or database schema changes.
- **Dependencies**: None planned — the timeline is built with existing styling (Tailwind), not a new charting library (see design.md for the alternatives considered).
