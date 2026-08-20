## 1. Domain model

- [x] 1.1 Add SQLAlchemy 2.x model `Skill` (id, name)
- [x] 1.2 Add an `employee_skills` join table (composite primary key of `employee_id`, `skill_id`, foreign keys to `Employee` and `Skill`) and a SQLAlchemy many-to-many `skills` relationship on `Employee`
- [x] 1.3 Add SQLAlchemy 2.x model `Contract` (id, customer_location_id, start_date, interval_days, duration_minutes) with a foreign key to `CustomerLocation`
- [x] 1.4 Add a `contract_skills` join table (composite primary key of `contract_id`, `skill_id`, foreign keys to `Contract` and `Skill`) and a SQLAlchemy many-to-many `required_skills` relationship on `Contract`
- [x] 1.5 Replace `ServiceVisit`'s `customer_location_id` and `duration_minutes` columns with a `contract_id` foreign key to `Contract`

## 2. Migration

- [x] 2.1 Create Alembic migration `0003` that: creates `skills`, `employee_skills`, `contracts`, and `contract_skills` tables; drops `service_visits.customer_location_id`/`duration_minutes` and adds `service_visits.contract_id` (fk to contracts, not null)
- [x] 2.2 Verify `alembic upgrade head` applies cleanly against a fresh Dockerized Postgres and the resulting schema matches the updated domain model

## 3. Backend API

- [x] 3.1 Update `EmployeeOut` schema and `GET /employees` to include each employee's skills (list of {id, name})
- [x] 3.2 Update `ServiceVisitOut` schema and `GET /service-visits` to nest the visit's contract (duration_minutes, required skills, and its customer location's customer name/address/region), sourced through the `contract`/`customer_location`/`customer`/`region`/`contract_skills` relations, with eager loading (`joinedload`) for the full chain
- [x] 3.3 Update `AssignmentOut`'s nested `employee` and `service_visit` payloads (used by `GET /assignments` and `POST /assignments`) to include the same skills/contract-derived fields
- [x] 3.4 Update `POST /assignments`'s `planned_end` computation to read `duration_minutes` from `visit.contract.duration_minutes` instead of the removed `visit.duration_minutes`

## 4. Seed data

- [x] 4.1 Update `backend/app/seed.py` to create a handful of `Skill` records
- [x] 4.2 Update the seed script's `Employee` creation to assign each employee zero or more skills via `employee_skills`
- [x] 4.3 Update the seed script to create `Contract` records (at least one per customer location, each with a `start_date`, `interval_days`, `duration_minutes`, and one or more required skills via `contract_skills`), replacing the previous direct `customer_location_id`/`duration_minutes` on `ServiceVisit`
- [x] 4.4 Update the seed script's `ServiceVisit` creation to generate a few occurrences per contract (dates derived from `start_date` and `interval_days`) referencing `contract_id` instead of `customer_location_id`/`duration_minutes`

## 5. Frontend

- [x] 5.1 Update `frontend/src/types.ts`: add a `Skill` type; add `skills: Skill[]` to `Employee`; replace `ServiceVisit.customer_location`/`duration_minutes` with a nested `contract` (duration_minutes, required_skills, and its `customer_location`) matching the updated API response
- [x] 5.2 Update the employee card (`EmployeeList`) to show the employee's skills as badges on the collapsed card, alongside its existing region badges
- [x] 5.3 Update the unassigned-visit card (`UnassignedVisitList`) to read region/duration through `visit.contract` instead of the removed `visit.customer_location`/`visit.duration_minutes`, show the visit's customer name directly on the collapsed card (above the badges), and show the visit's required skills as badges alongside the existing region badge (its info box already shows customer name, address, and GPS coordinates — no change needed there)
- [x] 5.4 Update the assigned-visit card (`AssignedVisitList`) to read region through `visit.contract.customer_location`, show the visit's customer name directly on the collapsed card (above the badges), show the visit's required skills as badges alongside the existing region badge, and add GPS coordinates to its info box (previously only customer name and address were shown there)

## 6. End-to-end verification

- [x] 6.1 Reset the Dockerized Postgres volume, run the new migration, run the updated seed script, and confirm `GET /employees` returns each employee's skills and `GET /service-visits` returns the expected contract-derived duration/customer/region/required-skills data
- [x] 6.2 Run the frontend against the backend and manually verify: employee and visit cards show skill badges, each visit card shows its customer name on the collapsed card, the assigned-visit card's info box now shows GPS coordinates (matching the unassigned card), and the existing assign flow (including double-assignment rejection) still works
