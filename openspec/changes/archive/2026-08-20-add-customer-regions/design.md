## Context

Current schema (from the `basic-manual-assignment` change): `employees`, `service_visits` (with flat `customer_name`, `address`, `latitude`, `longitude`), and `assignments`. The FastAPI backend exposes `GET /employees`, `GET /service-visits`, `GET/POST /assignments`, all backed by SQLAlchemy 2.x models and Alembic migrations. The React frontend renders three card lists (employees, unassigned visits, assigned visits) from those endpoints. See proposal.md - Why for the motivation to introduce `Region` and `Customer`/`CustomerLocation`.

## Goals / Non-Goals

**Goals:**
- Introduce `Region`, `Customer`, and `CustomerLocation` as first-class tables, with `ServiceVisit` generated from a `CustomerLocation` and `Employee` connected to one or more `Region`s via a many-to-many join table.
- Surface region (and, for visits, customer/address) on the existing list endpoints without adding new top-level endpoints.
- Add a click-to-expand info box on each of the three card types on the assignment page, showing the extra detail.
- Keep this backward-navigable in local dev: a fresh migration + reseed gets a working demo state.

**Non-Goals:**
- No CRUD API for regions, customers, or customer locations — they are only created by the seed script for this change. A management UI/API is future work.
- No region-based filtering, matching, or assignment logic (e.g. "only show employees in the visit's region") — this change is display-only.
- No historical snapshotting of customer/location data on the visit; if a `CustomerLocation` is edited later, past visits reflect the new data (there's no edit API yet, so this is not reachable today, but it's a conscious choice — see Decisions).

## Decisions

- **`ServiceVisit` drops its flat customer/location columns in favor of `customer_location_id`.** The user explicitly asked to remove them rather than keep a denormalized snapshot, since there's no visit-creation API yet (visits only come from the seed script) and duplicating the data would just be two sources of truth to keep in sync for no current benefit.
- **`Region` is a standalone entity**, not a free-text field on `Employee` or `CustomerLocation`. This matches the user's explicit choice and means the demo data (and any future region-based feature) has one canonical list of regions instead of drifting per-table strings.
- **Employee-to-Region is many-to-many, modeled with a join table (`employee_regions`: `employee_id`, `region_id`, composite primary key, FKs to both), not a list column on `Employee`.** An employee can belong to more than one region. A Postgres array or comma-separated column of region ids was considered and rejected: neither gives per-element referential integrity (nothing stops an array from containing an id that doesn't exist in `regions`), and both make "which employees are in region X" an awkward containment query instead of a plain join. The join table is the standard relational shape for many-to-many and matches SQLAlchemy's `relationship(..., secondary=...)` support directly. `CustomerLocation.region_id` stays a plain single-valued foreign key — only the employee side of this change needs multiplicity.
- **`Customer` and `CustomerLocation` are separate tables** (customer = billing/account identity, location = a serviceable address) even though this change only ever creates one flow through them (seed → visits). Splitting them now matches the user's stated model ("a customer can have 1 or more customer-locations") and avoids a later migration to split a merged table.
- **No new REST endpoints for regions/customers/locations.** Nothing in this change's UI needs to list customers or locations independently of a visit; region and customer/address are only ever shown nested inside `EmployeeOut` / `ServiceVisitOut`. Adding standalone endpoints now would be speculative.
- **Info box is inline expand-on-click per card, not a modal or hover tooltip.** Confirmed with the user. Implemented as local component state (`expanded: boolean`) on each card component — no new data fetching, since the info box only shows fields already present in the already-fetched employee/visit payload.
- **Migration drops and recreates `service_visits`' customer columns in one Alembic revision** (`0002`) alongside creating `regions`, `customers`, `customer_locations`, and adding `employees.region_id`. This is a dev-stage project with no production data to preserve, so a single straightforward revision (add new tables, alter existing ones, no data backfill) is simplest; the updated seed script repopulates everything after `alembic upgrade head`.

## Risks / Trade-offs

- [Breaking schema change to `service_visits`] → Acceptable pre-production; the README already documents "migrate then reseed" as the local dev flow, so this is consistent with existing practice, not a new risk class.
- [`CustomerLocation.region_id` NOT NULL] → Every location must have a region from the moment the row exists. Since the only writer is the seed script (no create API for these), this is enforceable in practice; if a future change adds location creation via API, that endpoint will need to require `region_id` too.
- [No DB-level guarantee every employee has at least one region] → A join table can't express "at least one row" as a column constraint the way a NOT NULL foreign key can. Nothing stops an employee row from existing with zero `employee_regions` rows. This is acceptable because the only writer is the seed script, which will always insert at least one region per employee; a future create-employee API would need to enforce this at the application layer.
- [Info box duplicates data already fetched] → No new network calls, but a card that later needs data *not* already in the list payload will need a real fetch-on-expand; today's fields (region, customer name/address) are all already present, so this is deferred, not designed around.
