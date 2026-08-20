## 1. Domain model

- [x] 1.1 Add SQLAlchemy 2.x model `Region` (id, name)
- [x] 1.2 Add SQLAlchemy 2.x model `Customer` (id, name)
- [x] 1.3 Add SQLAlchemy 2.x model `CustomerLocation` (id, customer_id, region_id, address, latitude, longitude) with foreign keys to `Customer` and `Region`
- [x] 1.4 Add an `employee_regions` join table (composite primary key of `employee_id`, `region_id`, foreign keys to `Employee` and `Region`) and a SQLAlchemy many-to-many `regions` relationship on `Employee`
- [x] 1.5 Replace `ServiceVisit`'s `customer_name`, `address`, `latitude`, `longitude` columns with a `customer_location_id` foreign key to `CustomerLocation`

## 2. Migration

- [x] 2.1 Create Alembic migration `0002` that: creates `regions` and `customers` tables; creates `customer_locations` (fk to customers, regions); creates `employee_regions` (composite pk of employee_id, region_id; fk to employees and regions); drops `service_visits.customer_name/address/latitude/longitude` and adds `service_visits.customer_location_id` (fk to customer_locations, not null)
- [x] 2.2 Verify `alembic upgrade head` applies cleanly against a fresh Dockerized Postgres and the resulting schema matches the updated domain model

## 3. Backend API

- [x] 3.1 Update `EmployeeOut` schema and `GET /employees` to include each employee's regions (list of {id, name})
- [x] 3.2 Update `ServiceVisitOut` schema and `GET /service-visits` to include the customer name, address, latitude/longitude, and region (id, name) of the visit's customer location, sourced through the `customer_location`/`customer`/`region` relations
- [x] 3.3 Update `AssignmentOut`'s nested `employee` and `service_visit` payloads (used by `GET /assignments` and `POST /assignments`) to include the same region/customer fields
- [x] 3.4 Update `POST /assignments` (and any other code constructing a `ServiceVisit`) for the new `customer_location_id` field in place of the removed flat columns

## 4. Seed data

- [x] 4.1 Update `backend/app/seed.py` to create a handful of `Region` records
- [x] 4.2 Update the seed script to create `Customer` and `CustomerLocation` records (each location assigned a region), replacing the previous flat visit customer/address/lat/long data
- [x] 4.3 Update the seed script's `ServiceVisit` creation to reference the seeded `customer_location_id` values instead of flat customer fields
- [x] 4.4 Update the seed script's `Employee` creation to associate each employee with one or more regions via `employee_regions`

## 5. Frontend

- [x] 5.1 Update `frontend/src/types.ts` with `Region`, and add nested region/customer fields to the `Employee` and `ServiceVisit` types matching the updated API responses
- [x] 5.2 Add a reusable expandable info-box UI piece (click to expand/collapse) usable by employee and visit cards
- [x] 5.3 Update the employee card (`EmployeeList`) to show its region(s) and use the info-box to reveal them on click
- [x] 5.4 Update the unassigned-visit card (`UnassignedVisitList`) to show its region and use the info-box to reveal customer name, address, and region on click
- [x] 5.5 Update the assigned-visit card (`AssignedVisitList`) to show its region and use the info-box to reveal customer name, address, and region on click

## 6. End-to-end verification

- [x] 6.1 Reset the Dockerized Postgres volume, run the new migration, run the updated seed script, and confirm `GET /employees` returns each employee's region(s) and `GET /service-visits` returns the expected customer/region data
- [x] 6.2 Run the frontend against the backend and manually verify: each employee card shows its region(s) and each visit card shows its region, clicking a card reveals the info box with the expected extra detail, and the existing assign flow (including double-assignment rejection) still works
