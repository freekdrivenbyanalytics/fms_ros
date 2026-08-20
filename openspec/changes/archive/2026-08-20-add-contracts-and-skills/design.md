## Context

Current schema (from `basic-manual-assignment` and `add-customer-regions`): `employees` (with `employee_regions` many-to-many to `regions`), `service_visits` (with `customer_location_id`, `duration_minutes`, `requested_date`, `status`), `assignments`, `regions`, `customers`, `customer_locations`. The FastAPI backend exposes `GET /employees`, `GET /service-visits`, `GET/POST /assignments`. The React frontend renders three card lists, each visit card with a click-to-expand info box. See proposal.md - Why for the motivation to introduce `Skill` and `Contract`.

## Goals / Non-Goals

**Goals:**
- Introduce `Skill` (many-to-many with `Employee`) and `Contract` (many-to-many with `Skill`, tied to a `CustomerLocation`) as first-class tables.
- Make `ServiceVisit` generated from a `Contract` rather than directly from a `CustomerLocation`, sourcing duration and required skills through that contract.
- Surface skills (on employees), and required skills/duration (on visits, via contract) on the existing list endpoints without adding new top-level endpoints.
- Show skills directly on employee and visit cards (alongside regions); add GPS coordinates to the assigned-visit card's info box to match the unassigned-visit card's.

**Non-Goals:**
- No runtime visit-generation mechanism (no "generate next visits" API/action, no scheduled job). Confirmed with the user: generation is seed-script-only for this change, same as customer-locations generating visits was seed-only before.
- No skill-based matching or filtering logic (e.g. "only allow assigning an employee who has the visit's required skills") — this change only makes the data visible, same scoping choice as regions.
- No contract CRUD API — contracts are only created by the seed script, matching the existing regions/customers/customer_locations precedent.
- No editing of existing contracts/skills.

## Decisions

- **`ServiceVisit.contract_id` replaces `ServiceVisit.customer_location_id`, and `ServiceVisit.duration_minutes` is dropped.** Confirmed with the user: a visit references its `Contract` only; `Contract.customer_location_id` is the single path to customer/location/region data, and `Contract.duration_minutes` is the single source for a visit's duration. This continues the "no denormalized snapshot" principle from `add-customer-regions` (drop the flat field, read through the relation) rather than copying duration onto each generated visit.
- **`interval_days: int` on `Contract`**, not an enum of "daily/weekly/monthly". A day-count is fully general (covers biweekly, monthly-ish, arbitrary custom cadences) and is trivial for the seed script to turn into concrete dates (`start_date`, `start_date + interval_days`, `start_date + 2*interval_days`, ...) without a calendar library.
- **`Contract.start_date: date`** is added (not in the user's original wording) so the seed script has a concrete anchor to generate deterministic visit dates from. This is a minor, non-scope-affecting addition needed to make "generates visits at an interval" actually seedable — noted here rather than asked, per the propose workflow's guidance to record minor assumptions rather than re-ask.
- **Employee-to-Skill is many-to-many via `employee_skills`, same shape as `employee_regions`.** Confirmed with the user. Unlike regions (every employee needs at least one, since it drives geographic assignment), skills are modeled as zero-or-more: an employee with no listed skills is valid (skills describe qualifications on top of baseline eligibility, not a required attribute), so there is no NOT-NULL-style "at least one" expectation to note as a risk here.
- **Contract-to-Skill is many-to-many via `contract_skills`.** A contract's required skills are read by visits through `contract.required_skills` — never stored per-visit, so a single edit to a contract's required skills would (if contracts were ever editable, which they are not in this change) apply uniformly to everything generated from it. This is the same reasoning as sourcing region/customer data through `CustomerLocation` rather than duplicating it onto each visit.
- **No new REST endpoints for skills or contracts.** Nothing in this change's UI needs to list contracts or skills independently of an employee or visit; they are only ever shown nested inside `EmployeeOut` / `ServiceVisitOut`. Matches the existing regions/customers precedent of not adding management endpoints speculatively.
- **Card UI**: skills are shown directly on the collapsed card for both employees (alongside regions) and visits (alongside region, sourced from the visit's contract's required skills) — confirmed with the user. Customer name is also shown on the collapsed visit card, above the region/skill badges — an initial draft of this design kept customer name info-box-only, but the user caught that as a regression while reviewing the implemented UI and asked for it back on the card. The assigned-visit card's info box gains GPS coordinates so both visit card types' info boxes show the same content (address and GPS coordinates, with customer name also still shown there).
- **Migration is a single Alembic revision (`0003`)** that creates `skills`, `employee_skills`, `contracts`, `contract_skills`, and alters `service_visits` (drop `customer_location_id`/`duration_minutes`, add `contract_id`). Same rationale as the `0002` migration: this is a dev-stage project with no production data, so a straightforward alter-in-place with no backfill is simplest, and the seed script repopulates everything after `alembic upgrade head`.

## Risks / Trade-offs

- [Breaking schema change to `service_visits`, again] → Same as the previous change: acceptable pre-production, consistent with the documented "migrate then reseed" local dev flow.
- [No DB-level guarantee every contract has at least one required skill] → Same limitation as the employee-region/employee-skill join tables: a join table can't express "at least one row" as a column constraint. Acceptable because the only writer is the seed script, which will always insert at least one skill per contract; a future contract-creation API would need to enforce this at the application layer.
- [Visit's duration and skill requirements are now two relations away (`visit → contract → duration_minutes` / `visit → contract → contract_skills → skill`)] → More joins per list query than before. At this data scale (a handful of seeded rows) this is not a real performance concern; the endpoint implementation should eager-load the chain (`joinedload`) the same way it already does for `customer_location → customer`/`region`, to avoid N+1s if the data set grows.
