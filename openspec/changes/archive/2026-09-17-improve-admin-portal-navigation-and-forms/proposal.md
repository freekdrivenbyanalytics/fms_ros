## Why

The four portal frontends (Planning, Admin Portal, Employee Management, Customer Portal) were built independently and never got a consistent way to move between them — only the main Planning app links out to the other three; none of the other three link back or to each other. Employee Management also lacks the "pick one or all" sidebar selector Customer Portal already has, employee editing has no fast way to grant every skill at once, the contract-line form's date/interval/duration fields have no visual grouping (unlike "Required products" right below them), and contract-line recurrence is limited to a raw day count, which can't cleanly express "every month" or "every quarter" (calendar months/quarters aren't fixed-length, so a day-count approximation drifts over time).

## What Changes

- Add the same cross-portal navigation links the main Planning app already has (`index.html`, `/customer-portal.html`, `/employee-management.html`, `/admin-portal.html`) to the Admin Portal, Employee Management, and Customer Portal sidebars, so every portal can reach every other one.
- Add a "Viewing as" selector to Employee Management's sidebar (one employee, or "All employees"), matching the pattern Customer Portal's `CustomerPortalApp.tsx` already uses.
- Add a "Select all skills" button to the employee create/edit form.
- Add a visual heading ("Schedule") above the contract-line form's start date/end date/interval/duration fields, matching the existing "Required products" heading below them.
- **BREAKING**: Replace a contract line's `interval_days: int` with `interval_unit` (`week`/`month`/`quarter`) + `interval_count` (a small integer, range depending on unit), so recurrence steps by real calendar months/quarters instead of an approximate day count. The allowed combinations are: every 1/2/3/4 week(s), every 1/2/3 month(s), or every quarter. Visit generation (`generate_occurrence_dates`/`extend_occurrence_dates`) becomes calendar-aware for month/quarter units instead of purely `timedelta`-based.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `admin-portal`: cross-portal navigation links; contract-line form gains a "Schedule" heading; contract-line create/update requirements reflect `interval_unit`/`interval_count`.
- `employee-management`: cross-portal navigation link; a "Viewing as" employee selector; a "select all skills" action on the employee form.
- `customer-portal`: cross-portal navigation link (no other behavior change in this capability — the dashboard itself is redesigned in a separate change).
- `contracts`: `Contract Line data model` and `Create, update, and soft-delete a contract line` change from `interval_days` to `interval_unit`/`interval_count`.
- `service-visits`: visit-generation requirements (`Creating a contract line generates its service visits`, `Open-ended contract lines' visit horizon can be topped up on demand`, `Updating a contract line regenerates its not-yet-started visits`) become calendar-unit-aware instead of day-interval-aware.

## Impact

- `backend/app/models.py`: `ContractLine.interval_days` replaced by `interval_unit` (string/enum) + `interval_count` (int).
- `backend/app/schemas.py`: `ContractLineCreate`/`ContractLineUpdate` swap `interval_days` for `interval_unit`/`interval_count`; a shared validator enforces the allowed-combination list server-side (not just in the UI).
- `backend/app/visit_generation.py`: `generate_occurrence_dates`/`extend_occurrence_dates` take `interval_unit`/`interval_count` instead of `interval_days`, stepping by real calendar months (clamping day-of-month, e.g. Jan 31 + 1 month → Feb 28/29) for `month`/`quarter` units, and by `timedelta(weeks=interval_count)` for `week`.
- A migration converts every existing contract line's `interval_days` to the nearest supported `interval_unit`/`interval_count` (today's only real value, 15 days, maps to "every 2 weeks" — a 1-day approximation, flagged in design.md).
- `frontend/src/types.ts`, `frontend/src/api.ts`: `ContractLineCreateInput`/`ContractLineUpdateInput`/`ContractLine` types updated; a shared constant lists the allowed unit/count combinations for the dropdown.
- `frontend/src/admin-portal/ContractsView.tsx`: interval fields become a unit+count dropdown pair; a "Schedule" heading added above the date/interval/duration fields.
- `frontend/src/employee-management/EmployeesView.tsx`, `EmployeeManagementApp.tsx`: "Viewing as" selector; "select all skills" button.
- `frontend/src/admin-portal/AdminPortalApp.tsx`, `frontend/src/employee-management/EmployeeManagementApp.tsx`, `frontend/src/customer-portal/CustomerPortalApp.tsx`: cross-portal nav links added to each sidebar.
