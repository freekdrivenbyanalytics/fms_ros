## 1. Cross-portal navigation links

- [x] 1.1 Add sidebar links to Planning, Customer Portal, and Employee Management in `frontend/src/admin-portal/AdminPortalApp.tsx`'s `<aside>`, matching the `<a href="...">` pattern already used in `frontend/src/App.tsx`
- [x] 1.2 Add sidebar links to Planning, Admin Portal, and Employee Management in `frontend/src/customer-portal/CustomerPortalApp.tsx`'s `<aside>`
- [x] 1.3 Add sidebar links to Planning, Customer Portal, and Admin Portal in `frontend/src/employee-management/EmployeeManagementApp.tsx`'s `<aside>`

## 2. Employee Management "viewing as" selector

- [x] 2.1 Add a `viewingAsEmployeeId: number | null` state and a `<select>` (one employee, or "All employees") to `EmployeeManagementApp.tsx`'s sidebar, copying `CustomerPortalApp.tsx`'s `viewingAsCustomerId` pattern
- [x] 2.2 Pass the selected id down to `EmployeesView.tsx` (or filter the `employees` list before passing it in) so the list shows only the selected employee, or every employee when "All employees" is selected. Done by filtering the `employees` array before passing it to `EmployeesView` (the simpler of the two documented options).

## 3. Employee form "select all skills"

- [x] 3.1 Add a "Select all skills" button to `EmployeesView.tsx`'s `EmployeeForm`, calling `setSkillIds(skills.map(s => s.id))` — no backend change needed (`EmployeeCreate`/`EmployeeUpdate` already accept an arbitrary `skill_ids` list)

## 4. Contract-line form heading

- [x] 4.1 Add a "Schedule" heading (matching the existing "Required products" heading's markup) above the start date/end date/interval/duration fields in `frontend/src/admin-portal/ContractsView.tsx`'s contract-line form

## 5. Backend: contract-line interval model

- [x] 5.1 Add a shared constant (e.g. `ALLOWED_CONTRACT_LINE_INTERVALS`) listing the supported `(interval_unit, interval_count)` pairs: `("week", 1..4)`, `("month", 1..3)`, `("quarter", 1)`, used by both the Pydantic validator and (indirectly, via the API) the frontend dropdown
- [x] 5.2 Replace `ContractLine.interval_days` with `interval_unit: Mapped[str]` and `interval_count: Mapped[int]` in `backend/app/models.py`
- [x] 5.3 Add an Alembic migration: add `interval_unit`/`interval_count` columns, backfill every existing row from its `interval_days` using the nearest-day-equivalent mapping in design.md, then drop `interval_days`. Migration `0021_contract_line_interval_unit.py` run successfully; confirmed all 150 demo contract lines backfilled to `week`/2 (from `interval_days=15`).
- [x] 5.4 Replace `interval_days: int` with `interval_unit`/`interval_count` in `ContractLineCreate`/`ContractLineUpdate`/`ContractLineOut` (`backend/app/schemas.py`); add a validator rejecting any pair not in the allowed set
- [x] 5.5 Add a stdlib-only `add_calendar_months(d: date, months: int) -> date` helper (clamping day-of-month via `calendar.monthrange`) to `backend/app/visit_generation.py`
- [x] 5.6 Update `generate_occurrence_dates`/`extend_occurrence_dates` in `backend/app/visit_generation.py` to take `interval_unit`/`interval_count` instead of `interval_days`: `week` steps by `timedelta(weeks=interval_count)`, `month`/`quarter` step by `add_calendar_months` (quarter = 3 × interval_count months). Promoted the shared stepping logic to a public `step_occurrence` helper (also reused by `seed.py`, see 5.7) rather than duplicating unit-dispatch logic. Later corrected during manual verification (7.3): occurrences are now anchored to the original `start_date` via `nth_occurrence` rather than iteratively stepped from the previous occurrence, to avoid permanent day-of-month drift after a clamp (see design.md). `extend_occurrence_dates` gained a `start_date` parameter for the same reason; both of its call sites in `main.py` updated to pass `line.start_date`.
- [x] 5.7 Update every caller of `generate_occurrence_dates`/`extend_occurrence_dates` (contract-line create/update endpoints, the extend-visits endpoint, `reset_demo_data.py`, `seed.py`) to pass `interval_unit`/`interval_count` instead of `interval_days`. `seed.py`'s manual 2-occurrence visit generation (which didn't call either function, just hand-computed `timedelta(days=occurrence * interval_days)`) also needed updating — switched it to the new `step_occurrence` helper.

## 6. Frontend: contract-line interval model

- [x] 6.1 Update `ContractLine`/`ContractLineCreateInput`/`ContractLineUpdateInput` types in `frontend/src/types.ts`: drop `interval_days`, add `interval_unit`/`interval_count`. Also added a `CONTRACT_LINE_INTERVAL_OPTIONS` constant (label + unit/count) mirroring the backend's allowed set, for the dropdown.
- [x] 6.2 Replace the interval number input in `ContractsView.tsx`'s contract-line form with a dropdown of the fixed allowed combinations (e.g. "Every week", "Every 2 weeks", ..., "Every quarter"), mapping each option to its `interval_unit`/`interval_count` pair
- [x] 6.3 Update anywhere else `interval_days` is displayed or read in the frontend (contract line list/detail rendering) to show the unit/count instead. Found and fixed three spots: the admin-portal contract-line row's summary line, and two customer-portal views (`ContractsView.tsx`, `CustomerLocationsView.tsx`) — each now via a local `formatInterval` helper reusing `CONTRACT_LINE_INTERVAL_OPTIONS`'s labels. Verified complete via `tsc -b` (build mode, not `tsc --noEmit`, which vacuously passes on this project's root `tsconfig.json` due to TS project references) — zero errors across the whole frontend.

## 7. Manual verification

- [x] 7.1 Confirm the migration backfills the existing ~150 demo contract lines' `interval_days: 15` to `interval_unit: "week"`, `interval_count: 2`. Verified via direct DB query: all 150 rows read `('week', 2)`.
- [x] 7.2 Create a contract line with each of the 8 supported interval combinations; confirm generated visit dates match (week-based: exact day counts; month/quarter-based: same day-of-month, N months later). Verified programmatically via `generate_occurrence_dates` for all 8 combinations — dates match expected cadence.
- [x] 7.3 Create a contract line starting January 31 with a monthly interval; confirm the next occurrence lands on February 28 (or 29 in a leap year), not an error or a rolled-forward date. Verified: Jan 31 → Feb 28. This surfaced a permanent-drift bug in the original implementation (Feb 28 → Mar 28 instead of Mar 31); fixed by anchoring every occurrence to the original `start_date` (see design.md and task 5.6). Re-verified after the fix: Jan 31 → Feb 28 → Mar 31 → Apr 30 → May 31 → Jun 30 → Jul 31.
- [x] 7.4 Attempt to create a contract line with an unsupported combination (e.g. every 5 weeks); confirm the request is rejected. Verified: `ContractLineCreate(interval_unit="week", interval_count=5, ...)` raises a `ValidationError` ("Unsupported interval: every 5 week(s)...").
- [x] 7.5 Click through all four portals' sidebars; confirm every portal links to every other portal and the links work. Verified live in browser: Planning links to Customer Portal/Employee Management/Admin Portal; Admin Portal, Customer Portal, and Employee Management each show an "Other portals" section linking to the other three; all navigations landed on the correct portal.
- [x] 7.6 Use Employee Management's "viewing as" selector to pick a specific employee, then "All employees"; confirm the list filters correctly. Verified live in browser: selecting "Alice Johnson" filtered the Employees list to just her row; switching back to "All employees" restored all three.
- [x] 7.7 Use the employee form's "select all skills" button; confirm every skill becomes checked and saves correctly. Verified live in browser: John Johnson started with only "Inspeksjon (vaktmester)" checked; clicking "Select all" also checked "Snømåking"; saved and confirmed persisted on the detail view.
- [x] 7.8 Confirm the contract-line form shows a "Schedule" heading above its date/interval/duration fields. Verified live in browser: the "SCHEDULE" heading appears above the start date/end date/interval dropdown/duration/priority fields, styled like "REQUIRED PRODUCTS" below it; the interval dropdown correctly showed "Every 2 weeks" for the line's stored `week`/2 value.
