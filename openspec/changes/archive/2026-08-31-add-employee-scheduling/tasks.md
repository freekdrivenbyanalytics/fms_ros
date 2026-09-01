## 1. Backend data model & migration

- [x] 1.1 In `backend/app/models.py`: add `delete_flag` to `Employee`; remove `work_start`/`work_end`; add `EmployeeScheduleTemplate` (id, employee_id, start_date, end_date nullable, work_start, work_end, max_hours_per_day, lunch_type enum [none/fixed/flexible], lunch_start nullable, lunch_end nullable, lunch_duration_minutes nullable, delete_flag) and `EmployeeScheduleDayOverride` (id, employee_id, date, day_type enum [working/holiday/sick], work_start nullable, work_end nullable, max_hours_per_day nullable, overtime_minutes nullable, delete_flag), each with a relationship back to `Employee`.
- [x] 1.2 New Alembic migration `0008_employee_scheduling.py`: create the two new tables and their enum types (following the `values_callable` pattern used for `VisitStatus`/`CustomerChangeType`); add `employees.delete_flag`; backfill one open-ended `EmployeeScheduleTemplate` per existing employee row from its current `work_start`/`work_end` (default `max_hours_per_day=8`, `lunch_type=none`) before dropping `employees.work_start`/`work_end`. Write a `downgrade()` that re-adds the dropped columns (nullable) and drops the new tables.
- [x] 1.3 Run `alembic upgrade head`, then `alembic downgrade 0007`, then `alembic upgrade head` again to confirm both directions work cleanly against the running Postgres container.

## 2. Backend schedule resolution & validation

- [x] 2.1 Add `resolve_employee_schedule(db, employee_id, target_date) -> tuple[time, time] | None` implementing the override → template → none precedence from `employees` spec's "An employee's effective schedule for a date is resolved from overrides and templates" (a `holiday`/`sick` override returns `None`; a `working` override with its own hours returns those; a `working` override without hours falls back to the covering template; no override falls back to the covering template; nothing covers the date returns `None`). This function reads only `work_start`/`work_end` — never `overtime_minutes` — so both validation and the solver payload stay overtime-blind automatically (design.md D6.5).
- [x] 2.2 Add validation helpers: reject a template create/update whose date range overlaps another non-deleted template for the same employee; reject a second non-deleted override for the same employee+date; reject a template or working-override whose `work_end - work_start` exceeds its effective max-hours-per-day (its own `max_hours_per_day` for a template, or the override's own value else the covering template's value for an override).

## 3. Backend API

- [x] 3.1 Add `EmployeeOut`/`EmployeeCreate`/`EmployeeUpdate`, `EmployeeScheduleTemplateOut`/`Create`/`Update`, `EmployeeScheduleDayOverrideOut`/`Create`/`Update` schemas in `backend/app/schemas.py` matching the data models (`EmployeeOut` nests templates and day overrides, excluding soft-deleted ones).
- [x] 3.2 Add `POST /employees`, `PATCH /employees/{id}`, `DELETE /employees/{id}` (soft) in `backend/app/main.py`; update `GET /employees` to exclude `delete_flag=True` by default and to stop returning `work_start`/`work_end`.
- [x] 3.3 Add `POST /employees/{id}/schedule-templates`, `PATCH /schedule-templates/{id}`, `DELETE /schedule-templates/{id}` (soft), applying the 2.2 validations and returning 422 on violation.
- [x] 3.4 Add `POST /employees/{id}/schedule-overrides`, `PATCH /schedule-overrides/{id}`, `DELETE /schedule-overrides/{id}` (soft), accepting and returning `overtime_minutes` alongside regular hours, and applying the 2.2 validations to regular hours only (never to `overtime_minutes`); add `POST /employees/{id}/schedule-overrides/bulk` accepting a date range + day_type to create one override per date (for the "quickly mark holidays/sickness" requirement).
- [x] 3.5 Add `GET /employees/{id}/schedule-templates` and `GET /employees/{id}/schedule-overrides` list endpoints excluding soft-deleted rows.

## 4. Backend seed data

- [x] 4.1 Update `backend/app/seed.py`: stop setting `work_start`/`work_end` on seeded employees; instead create one open-ended `EmployeeScheduleTemplate` per seeded employee (e.g. 08:00-16:00, max_hours_per_day=8, lunch_type=none) and a couple of sample `EmployeeScheduleDayOverride` rows (e.g. one holiday, one manually-adjusted working day) to exercise the resolution logic.
- [x] 4.2 Re-run seeding against a fresh database and confirm employees, templates, and overrides are created without warnings (watch for the same "not in session" pitfall hit in `add-contract-lines` — add each object to the session immediately after construction).

## 5. Solver domain & constraints

- [x] 5.1 In `solver/app/domain.py`: remove `work_start_minutes`/`work_end_minutes` from the `Employee` dataclass; add a new frozen dataclass `EmployeeDaySchedule(employee_id, date, start_minutes, end_minutes)`; add it to `Schedule` as a plain `ProblemFactCollectionProperty` (not a value range).
- [x] 5.2 In `solver/app/constraints.py`: replace `_outside_working_hours` with a join-based hard constraint against `EmployeeDaySchedule` (join on employee id + requested_date, penalize when the visit's window is not fully contained in the schedule's window); add a new hard constraint using `if_not_exists` against `EmployeeDaySchedule` (same joiners) to penalize a visit assigned to an employee with no schedule that date.
- [x] 5.3 Manually verify the two new/changed constraints in isolation (small script constructing a `Schedule` with a couple of `EmployeeDaySchedule` facts and visits) before wiring into the full payload, per design.md's risk note on `if_not_exists`.

## 6. Solver client integration

- [x] 6.1 In `backend/app/solver_client.py`: for every distinct (employee, date) pair appearing in the payload (candidate visit dates, existing-assignment dates), call `resolve_employee_schedule` (2.1) and build the corresponding `EmployeeDaySchedule` payload entries; skip pairs that resolve to `None` (no schedule) rather than sending a null-hours fact.
- [x] 6.2 Update the solver-side Pydantic request schema (`solver/app/schemas.py`) to accept the new `employee_day_schedules` list, and remove `work_start_minutes`/`work_end_minutes` from the employee payload schema.
- [x] 6.3 Update `backend/app/solver_client.py`'s employee-payload builder to stop sending `work_start`/`work_end` and instead send the new `employee_day_schedules` list built in 6.1.

## 7. Frontend shared components

- [x] 7.1 Move `ListTable.tsx` and `DetailField.tsx` from `frontend/src/customer-portal/` to a new `frontend/src/shared/` directory; update imports in the Customer Portal views.

## 8. Frontend: new Employee Management area

- [x] 8.1 Add `employee-management.html` at the project root (mirroring `customer-portal.html`) and register it in `vite.config.ts`'s `rollupOptions.input`.
- [x] 8.2 Create `frontend/src/employee-management/main.tsx` and `EmployeeManagementApp.tsx` providing its own top-level layout with no Planning or Customer Portal navigation, and an `EmployeesView` list/detail using the shared `ListTable`/`DetailField`.
- [x] 8.3 Implement employee CRUD forms (create/update/soft-delete) covering name, location, regions, and skills.
- [x] 8.4 Implement schedule template CRUD (create/update/soft-delete) on the employee detail view, including client-side surfacing of the overlap/over-cap validation errors from 3.3.
- [x] 8.5 Implement day override CRUD (create/update/soft-delete) on the employee detail view, plus a "mark holiday/sick" control that calls the bulk endpoint (3.4) for a single date or a date range.
- [x] 8.5.1 Add an overtime-minutes input to the working-day override form, labeled to indicate it is not currently used by the route optimizer, per the `employee-management` delta spec's "Record overtime for a day from Employee Management".
- [x] 8.6 Add `frontend/src/types.ts` and `frontend/src/api.ts` entries for `Employee`, `EmployeeScheduleTemplate`, `EmployeeScheduleDayOverride` and their CRUD calls, replacing any existing static-hours employee type.

## 9. Frontend: remove Employees from the Customer Portal

- [x] 9.1 Delete `frontend/src/customer-portal/EmployeesView.tsx` and remove the Employees list/detail route and nav entry from `CustomerPortalApp.tsx`.
- [x] 9.2 Update `SkillsView.tsx` and `RegionsView.tsx` (Customer Portal) to drop the "Employees who possess it" / "Employees scoped to it" sections from their detail views, per the `customer-portal` delta spec.
- [x] 9.3 Remove any now-unused employee fetching/state from `CustomerPortalApp.tsx`.

## 10. End-to-end verification

- [x] 10.1 Verify via API: creating an overlapping template is rejected (422); creating a second override for the same employee+date is rejected; a working override/template exceeding its effective max-hours-per-day is rejected.
- [x] 10.2 Verify via API: an employee with a holiday override on a date is excluded from proposals for visits on that date even when otherwise qualified; an employee with no template/override at all for a visit's date is excluded the same way.
- [x] 10.3 Verify via API: a visit whose requested date falls within a manually-overridden day (different hours than the template) is only proposed within the override's window, not the template's.
- [x] 10.3.1 Verify via API: setting a large `overtime_minutes` value on a day override does not widen the window a proposed schedule will place visits in for that date, and does not get rejected by the max-hours-per-day validation regardless of how large it is.
- [x] 10.4 Launch frontend + backend and manually confirm in the browser: Employee Management is reachable as its own top-level page with no Planning/Customer Portal nav; employee CRUD and schedule template/override CRUD work end-to-end; the Customer Portal no longer shows Employees anywhere (nav, lists, Skill/Region detail views).
- [x] 10.5 Confirm `openspec validate --strict` passes for the change before archiving.
