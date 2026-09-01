## Why

Employee masterdata is currently a read-only entry in the Customer Portal, and every employee is assumed to work the same static `work_start`/`work_end` window every day forever. That's no longer enough: employees need real calendars — a default weekly template for a date range, manual day-by-day overrides for a different shift, holidays, sickness, and a per-day hours cap — and the route optimizer needs to schedule against the employee's *actual* hours for the visit's date, not a single fixed window. Employee management also doesn't belong in a customer-facing portal; it's internal planning data and needs full CRUD, which the read-only portal is not built for.

## What Changes

- **BREAKING**: Remove the Employees list/detail view and all employee data from the Customer Portal. Employees are no longer visible or manageable there.
- Add a new, separate top-level frontend area ("Employee Management") — its own entry point, sharing no navigation with Planning or the Customer Portal — for managing employees and their schedules.
- Add full CRUD (create, update, soft-delete) for employees from this new area: name, home location, regions, and skills. Soft-delete follows the existing `delete_flag` pattern used by customers/contracts.
- **BREAKING**: Drop `Employee.work_start`/`work_end`. An employee's working hours are no longer static; they're resolved per date from schedule templates and day overrides.
- Add an `EmployeeScheduleTemplate` entity: a work-hours window (start/end), a max-hours-per-day cap, and lunch fields (type: none/fixed/flexible, start/end/duration — captured but not yet used by the solver), all bounded by a start/end date range. An employee can have multiple templates but their date ranges must not overlap.
- Add an `EmployeeScheduleDayOverride` entity: a single date with a day type (working / holiday / sick). A "working" override may supply its own regular hours and its own max-hours-per-day cap, for one-off shift changes; holiday/sick overrides carry no hours.
- Add an overtime field on a day override: extra minutes worked beyond the override's regular hours, recorded from the Employee Management area. Overtime is **not** used by the route optimizer in this change — only an override's regular hours are ever solver-visible. Prioritizing and long-term-planning around overtime is deferred to a later iteration.
- Add CRUD for both schedule entities from the Employee Management area, including "generate templates" (apply a template to a date range) and per-day manual overrides.
- Add write-time validation: a day's effective *regular* hours (whether from an override or a template) can never exceed that day's effective max-hours-per-day cap. Overtime is excluded from this check for now, since how overtime interacts with the cap is part of the deferred later iteration.
- Update the route optimizer to resolve each employee's working hours per visit date (override's regular hours, else covering template, else the employee has no schedule that day and cannot be assigned any visit that day), replacing the static working-hours check. Lunch and overtime are explicitly out of scope for the solver in this change.

## Capabilities

### New Capabilities
- `employee-management`: the standalone frontend area for managing employees and their schedules — its separateness from Planning/Customer Portal, its list/detail views, and the CRUD actions available from it.

### Modified Capabilities
- `employees`: data model changes (drop static hours, add soft-delete), new schedule-template and day-override data models and their CRUD/validation rules, and the schedule-resolution rule the solver depends on.
- `route-optimization`: the "working hours" hard constraint becomes date-dependent (resolved per employee per visit date) instead of a single static window, and gains a new exclusion for an employee with no resolved schedule on the visit's date.
- `customer-portal`: remove Employees from the portal's entity list, list views, detail views, and every requirement/scenario that names it.

## Impact

- Backend: new `employee_schedule_templates` and `employee_schedule_day_overrides` tables (new migration), `Employee` loses `work_start`/`work_end` and gains `delete_flag`; new schemas/endpoints for employee CRUD and both schedule entities; `solver_client.py` gains per-employee-per-date schedule resolution and a new problem fact type; seed data rebuilt to generate templates/overrides instead of static hours.
- Frontend: new top-level entry point + app (mirroring `customer-portal.html`'s pattern) for Employee Management, with its own list/detail/CRUD views for employees and their schedules; `CustomerPortalApp`/`EmployeesView` and related employee code removed from the Customer Portal.
- No changes to Manual Assignment or Day Planning views themselves beyond the optimizer now respecting date-dependent hours.
