## Why

Right now every service visit is a one-off, manually assignable unit tied only to a customer location, and any employee can be picked for any visit regardless of what work it actually requires. Real service work is often recurring (a customer under a maintenance contract gets visited every N days) and skill-gated (a visit needs an employee qualified to do it). Introducing `Skill` (on employees and on a new `Contract`) and `Contract` (a recurring agreement tied to a customer location that visits are generated from) lets a visit describe what it actually requires and lets the assignment page surface that, instead of matching being purely manual and skill-blind as it is today.

## What Changes

- Add a `Skill` domain model (id, name).
- Add a many-to-many relationship between `Employee` and `Skill` (an employee can have more than one skill), backed by an `employee_skills` join table.
- Add a `Contract` domain model (id, customer_location_id, start_date, interval_days, duration_minutes) representing a recurring service agreement tied to a customer location.
- Add a many-to-many relationship between `Contract` and `Skill` (a contract can require more than one skill), backed by a `contract_skills` join table — this is where a service visit's skill requirements are described.
- **BREAKING**: `ServiceVisit` no longer references a `CustomerLocation` directly, and drops its own `duration_minutes`. It instead references a `Contract` via `contract_id`; customer/location/region and duration are read through `contract.customer_location` and `contract.duration_minutes`, and skill requirements are read through `contract.required_skills`.
- Extend the seed script to generate demo `Skill` records, assign skills to employees, create a `Contract` per (or per some) customer location with required skills, and generate service visits from those contracts at their interval instead of directly from customer locations. No runtime "generate visits" mechanism is added — generation is seed-script-only for this change, same as customer locations generating visits was seed-only before.
- Show skills directly on cards: each employee card shows its skills as badges alongside its regions, and each visit card shows its contract's required skills as badges alongside its region. Each visit card also shows its customer name directly (above the region/skill badges).
- Add GPS coordinates to the assigned-visit card's info box, matching what the unassigned-visit card's info box already shows (it was previously missing from the assigned card). Both visit card types' info boxes show address and GPS coordinates (customer name is also repeated there, having originally been the only thing the unassigned card's info box showed).

## Capabilities

### New Capabilities
- `skills`: `Skill` domain model — a named qualification referenced by employees and contracts.
- `contracts`: `Contract` domain model — a recurring service agreement tied to a customer location, with required skills, from which service visits are generated at a fixed interval.

### Modified Capabilities
- `employees`: employees now carry a many-to-many set of skills.
- `service-visits`: visits are now generated from a `Contract` rather than directly from a `CustomerLocation`; duration and skill requirements are sourced through the contract.
- `assignments`: employee cards show skills directly (alongside regions); visit cards show customer name and required skills directly (alongside region); the assigned-visit card's info box also shows GPS coordinates, matching the unassigned card.

## Impact

- Backend: new `skills`, `employee_skills`, `contracts`, and `contract_skills` tables, a new Alembic migration altering `service_visits` (drop `customer_location_id` and `duration_minutes`, add `contract_id`), updated Pydantic schemas and endpoint responses (employee/visit payloads now include skills and, for visits, the required skills and contract-derived duration), updated seed script.
- Frontend: updated types/API client for skills and contract-derived fields, and card layout changes (skill badges on employee and visit cards, GPS added to the assigned card's info box).
- No new top-level API endpoints are required; skill/contract data is exposed only through the existing employees/service-visits/assignments responses. No visit-generation endpoint or background job is added in this change.
