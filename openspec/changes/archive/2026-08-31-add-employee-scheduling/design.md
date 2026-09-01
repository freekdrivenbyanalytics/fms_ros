## Context

See proposal.md - Why. Today `Employee` (backend/app/models.py) has static `work_start`/`work_end` columns, and the solver's own `Employee` fact (solver/app/domain.py) carries `work_start_minutes`/`work_end_minutes` directly. That solver `Employee` object is also the **value-range candidate** for `VisitAssignment.employee` (`ValueRangeProvider(id="employee_range")`) — the same instance is reused across every visit the solver considers assigning to that employee, regardless of the visit's date. Making hours date-dependent therefore cannot be done by adding fields to that class; a single `Employee` fact has no date to key off. This shapes decision D3 below.

The Customer Portal (`frontend/src/customer-portal/`) and its Vite multi-entry setup (`customer-portal.html` + `vite.config.ts` `rollupOptions.input`) is the direct precedent for the new Employee Management area, including its `ListTable`/`DetailField` presentational components.

## Goals / Non-Goals

**Goals:**
- Replace static employee hours with a per-employee-per-date resolution (override → template → none) that the solver enforces as a hard constraint.
- Give Employee Management full CRUD for employees and both schedule sub-entities, as its own top-level frontend area.
- Enforce the max-hours-per-day cap without adding a new runtime aggregation constraint.

**Non-Goals:**
- Lunch is captured in the data model but not consumed by the solver in this change (per proposal).
- Overtime is captured on day overrides but not consumed by the solver in this change; using it to prioritize or long-term-plan schedules is deferred to a later iteration (per proposal).
- No calendar-grid/drag-and-drop UI — list/form based CRUD, consistent with the Customer Portal's existing UI complexity.
- No change to Manual Assignment or Day Planning's own UI; only the schedule feeding the optimizer changes.

## Decisions

### D1: Two new tables, not a single "schedule" table
`employee_schedule_templates` (period-bounded) and `employee_schedule_day_overrides` (single-date) are separate tables rather than one polymorphic table, because their cardinality and validation rules differ (templates: no date-range overlap per employee; overrides: at most one per employee+date) and a single table would need nullable-everything columns plus a discriminator to tell them apart. Both get their own `delete_flag`, following the established soft-delete pattern (`Customer`, `CustomerLocation`, `Contract`, `ContractLine`).

### D2: Max-hours-per-day is enforced by write-time validation, not a solver constraint
Alternative considered: a Timefold `group_by` aggregation constraint summing an employee's assigned minutes per day and penalizing over the cap. Rejected because `group_by`-based aggregation constraints are unproven in this codebase (every existing hard constraint here is a `for_each`/`for_each_unique_pair`/`join` filter, never an aggregation), and because the cap is redundant with the working-hours window once that window itself cannot exceed the cap: if every override/template is validated so `work_end - work_start <= effective_max_hours_per_day` at write time (new `employees` requirement "A day's effective hours cannot exceed its effective max hours per day"), then the existing "time window falls entirely within working hours" + "no overlap between an employee's visits" constraints already guarantee the employee's total scheduled time that day cannot exceed the cap. This still satisfies "solver enforces the daily hours cap now" (the user's answer) — the cap is baked into the window the solver's existing hard constraint enforces — without adding new solver-side risk.

### D3: Replace the solver's static `Employee.work_*_minutes` with a per-date fact, joined like `ExistingAssignmentFact`
Drop `work_start_minutes`/`work_end_minutes` from the solver's `Employee` dataclass (domain.py) — it stays the value-range identity object (id, skill_ids, region_ids, lat/long) only. Add a new frozen dataclass `EmployeeDaySchedule(employee_id, date, start_minutes, end_minutes)` as a plain `ProblemFactCollectionProperty` (not a value range — it's data, never assigned). `solver_client.py` builds one `EmployeeDaySchedule` per employee per distinct date appearing in the payload (candidate visits' requested/rescheduled dates plus existing-assignment dates), by calling the same resolution logic the backend already uses for write-time validation (D2), exposed as a shared function.

Constraint changes in `solver/app/constraints.py`:
- Replace `_outside_working_hours` (which read `visit.employee.work_start_minutes`) with a join: `for_each(VisitAssignment).filter(_is_scheduled).join(EmployeeDaySchedule, Joiners.equal(employee_id, employee_id), Joiners.equal(requested_date, date)).filter(window not contained in schedule).penalize(...)`.
- Add a new hard constraint for "no schedule that date": `for_each(VisitAssignment).filter(_is_scheduled).if_not_exists(EmployeeDaySchedule, Joiners.equal(employee_id, employee_id), Joiners.equal(requested_date, date)).penalize(...)`. Verified during design: this installed Timefold version's `UniConstraintStream` exposes `if_not_exists`/`if_exists` (and `_other` variants), so this is a supported API, not a discovery spike.

This mirrors the already-proven `ExistingAssignmentFact` cross-class join pattern (`Joiners.equal` on employee, `Joiners.equal`/`Joiners.overlapping` on date/time) used elsewhere in this file.

### D4: Backend resolution logic lives in one place, used by both validation and the solver payload
A single function (e.g. `resolve_employee_schedule(db, employee_id, date) -> (start, end) | None`) implements the override→template→none precedence from the `employees` spec. Write-time validation (creating/updating a template or override) and `solver_client.py`'s per-date `EmployeeDaySchedule` construction both call it, so the resolution rule is defined once.

### D5: Employee Management is a new Vite entry, mirroring the Customer Portal
Add `employee-management.html` + `frontend/src/employee-management/` (own `main.tsx`, `EmployeeManagementApp.tsx`, `EmployeesView.tsx`, `ScheduleTemplatesView.tsx`/`DayOverridesView.tsx` or a combined per-employee schedule panel), registered in `vite.config.ts`'s `rollupOptions.input` next to `customerPortal`. `ListTable` and `DetailField` move from `src/customer-portal/` to a shared location (e.g. `src/shared/`) since both portal-style apps now use them; `EmployeesView.tsx` and its employee-specific logic are deleted from `src/customer-portal/` entirely, not shared.

### D6.5: Overtime is a recorded-only field, kept out of `resolve_employee_schedule`'s solver-facing output
`EmployeeScheduleDayOverride` gets an `overtime_minutes` column (nullable, only meaningful when `day_type = working`), separate from `work_start`/`work_end`. This keeps "regular hours" (solver-visible, validated against the max-hours-per-day cap) and "overtime" (recorded, not yet solver-visible, not yet validated against any cap) as distinct fields rather than overloading `work_end` to silently include overtime. `resolve_employee_schedule` (D4) never reads `overtime_minutes` — it returns only `work_start`/`work_end` (own or inherited from the covering template) — so both the write-time validation path and the solver's `EmployeeDaySchedule` construction automatically stay overtime-blind without a separate code path. Alternative considered: extend `work_end` itself to include overtime and have the solver-payload builder subtract it back out before building `EmployeeDaySchedule`. Rejected because it would make `work_end` mean different things to different readers (validation vs. solver vs. UI) and risks a future change accidentally letting overtime leak into the solver-visible window by omitting the subtraction step.

### D6: `Employee.work_start`/`work_end` are dropped with no fallback
No employee keeps working under the old static hours after this migration; every employee needs at least one schedule template (or explicit day overrides) going forward. The migration seeds a single open-ended template per existing employee from their current `work_start`/`work_end` (see Migration Plan) so nothing silently loses its schedule.

## Risks / Trade-offs

- [Risk] An employee with no template/override for a date becomes unschedulable that date, which could silently shrink solver feasibility if templates aren't set up for far-future dates. → Mitigation: migration backfills an open-ended (`end_date = NULL`) template per employee from current hours, so coverage is at least as good as today until someone narrows it.
- [Risk] `if_not_exists`/`if_exists` is less commonly used in this codebase than `for_each`/`join`/`filter`. → Mitigation: already verified against the installed Timefold version during design (see D3); apply-phase task includes a focused unit/manual verification of just this constraint before wiring it into the full payload.
- [Trade-off] Write-time-validation-only enforcement of the max-hours cap (D2) means the cap is only as good as every write path checking it; a future direct-DB write could bypass it. Accepted as consistent with how every other invariant in this codebase (e.g. contract line dates) is enforced — API-layer validation, not DB constraints.

## Migration Plan

1. New Alembic migration adds `employee_schedule_templates` and `employee_schedule_day_overrides` tables, adds `delete_flag` to `employees`, and drops `employees.work_start`/`work_end`.
2. Because dropping columns employees still depend on is structural, follow the established truncate-and-rebuild pattern used in migrations 0004/0006/0007: within the same migration, for each existing employee row, insert one `employee_schedule_templates` row with `start_date = NULL`-equivalent earliest sentinel (use today's date as `start_date`, `end_date = NULL`) and `work_start`/`work_end`/a reasonable default `max_hours_per_day` (e.g. 8) copied from the row being dropped, before dropping the columns. This is additive data migration, not a destructive truncate — no assignments/visits need to be cleared for this change.
3. `seed.py` updated to generate a template per seeded employee (and optionally a couple of sample day overrides) instead of setting `work_start`/`work_end` directly.
4. Rollback: `downgrade()` re-adds `work_start`/`work_end` (nullable, since there's no single template to collapse back down deterministically) and drops the new tables; acceptable since this is a dev-seed-driven project, matching precedent from prior migrations in this repo.

## Open Questions

None — the two ambiguities that would have changed the approach (whether `if_not_exists` is available, and how to enforce max-hours-per-day) were resolved during this design.
