## Context

The frontend (`frontend/src/App.tsx`) is a single view with no router — see `frontend/package.json`, which lists only `react`/`react-dom`, no `react-router` or charting library. It fetches `listEmployees()`, `listServiceVisits()`, `listAssignments()` from `frontend/src/api.ts` on mount and renders three card lists. `Assignment` (`frontend/src/types.ts`) already carries `employee` (with `skills`), `service_visit` (with `contract.customer_location.customer/address/region`, `contract.required_skills`), `planned_start`, `planned_end` — everything the chart and its detail expansion need is already returned by the existing `GET /assignments` endpoint. The app already has an expand-on-click pattern (`frontend/src/components/InfoBox.tsx`) used by `EmployeeList` and `AssignedVisitList` for exactly this kind of compact-label-plus-detail card. See proposal.md - Why / What Changes for motivation and scope.

## Goals / Non-Goals

**Goals:**
- Add the day-planning view without a routing library or a charting/Gantt library, keeping the dependency footprint unchanged.
- Reuse the existing `listAssignments`/`listEmployees` API calls unmodified.

**Non-Goals:**
- No new backend endpoint or query parameter for date filtering — the assignment list is small enough (single-tenant demo scale) to filter client-side.
- No persistence of the selected date or the chosen view across reloads (always resets to the assignment page + today).

## Decisions

- **View switch, not a router.** Add a small `view` state (`"assign" | "planning"`) in `App.tsx` with two nav buttons, instead of adding `react-router-dom`. Alternative considered: introduce a router — rejected as disproportionate for two top-level views and a new dependency the proposal explicitly avoids.
- **Client-side date filtering.** Fetch assignments once (existing behavior) and filter in the new page component by comparing `planned_start`'s local calendar date to the selected date. Alternative considered: a `GET /assignments?date=` backend filter — rejected for now since it would touch the backend and existing data volume doesn't need it; can be revisited if assignment volume grows.
- **CSS-grid timeline, not a charting library.** Render one shared CSS grid spanning the visible work-hours window (e.g., 06:00–20:00), with every employee as a row inside that single grid and each assignment block absolutely positioned by percentage offset computed from `planned_start`/`planned_end`. All employees render inside this one grid element — never one grid instance per employee — so the chart is a single scannable surface, not N side-by-side charts. Alternative considered: a charting/Gantt library (e.g., vis-timeline) — rejected per the proposal's stated no-new-dependency intent; the layout math is straightforward for a fixed-day, non-interactive view.
- **Reuse `InfoBox` for block detail, reuse skill-pill styling for row labels.** Each timeline block's compact label (customer name) is the `InfoBox` summary; expanding it shows the visit's customer, address, region, and required skills, plus planned start/end — mirroring `AssignedVisitList`'s existing card exactly, just inside a timeline block instead of a list item. Each employee row label renders the employee's name plus skill pills styled like `EmployeeList`'s skill badges. Alternative considered: inventing a new tooltip/popover component — rejected since it would introduce a second, inconsistent detail-disclosure pattern alongside the one already used elsewhere in the app.
- **New top-level component, e.g. `frontend/src/components/DayPlanningView.tsx`,** owning the date state and doing the filtering, kept alongside the existing list components rather than restructuring `App.tsx` beyond the new view switch.

## Risks / Trade-offs

- [Fixed work-hours window may clip an assignment that starts before or ends after the window] → Clamp block rendering to the visible window edges rather than hiding the block, so an out-of-window assignment is still visible (truncated) rather than silently dropped.
- [Client-side filtering re-scans the full assignment list on every date change] → Acceptable at current data scale (see Non-Goals); no action needed now.
- [A narrow timeline block (short assignment) has little room for its expanded `InfoBox` detail, and expanding one block inline could shift or overlap neighboring rows] → Expand the detail as an overlay positioned relative to the block (not inline document flow), so expansion never resizes the row grid itself.
