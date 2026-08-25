## 1. View Switch

- [x] 1.1 Add a `view` state (`"assign" | "planning"`) to `App.tsx` with two nav buttons/tabs to switch between the existing manual-assignment page and the new day-planning page.

## 2. Day Planning Component

- [x] 2.1 Create `frontend/src/components/DayPlanningView.tsx` accepting `employees` and `assignments` and owning the selected-date state, defaulting to today.
- [x] 2.2 Add a date control (previous/next buttons plus a date picker) that updates the selected date.
- [x] 2.3 Filter assignments to those whose `planned_start` falls on the selected local calendar date.
- [x] 2.4 Render a single shared CSS grid (one chart, not one grid per employee) with one row per employee, spanning a fixed visible-hours window (e.g., 06:00-20:00).
- [x] 2.5 For each employee's filtered assignments, render a timeline block positioned by percentage offset within the window, clamped to the window edges, labeled with the assignment's `service_visit.contract.customer_location.customer.name`.
- [x] 2.6 Wrap each block's label in the existing `InfoBox` component so it expands (as an overlay, not inline) to show the visit's customer name, address, region, required skills, and the assignment's planned start/end.
- [x] 2.7 Render each employee row's label with the employee's name plus skill pills, styled like `EmployeeList`'s skill badges.
- [x] 2.8 Render an empty (blockless) row for an employee with no assignments on the selected date.
- [x] 2.9 Ensure no create/edit/delete affordance exists on any timeline block (read-only) — the `InfoBox` expand is a detail view only.

## 3. Wiring

- [x] 3.1 Wire `DayPlanningView` into `App.tsx` under the new "planning" view, passing the already-fetched `employees` and `assignments` state (no new API calls).

## 4. Verification

- [x] 4.1 Run the frontend dev server and manually verify: default day is today, prev/next and date picker change the shown assignments, an employee with no assignments that day shows an empty row, all employees appear as rows in one combined chart (not separate charts), each employee row shows that employee's skills, expanding a block shows full visit/location/skill detail, and no editing action is available from the page.
