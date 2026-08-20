## Why

Service visits currently store customer/location details flat on the visit itself, with no notion of a customer having multiple locations or of geographic regions. Planners need to see which region an employee or visit belongs to at a glance, and need a way to see more detail on a card without leaving the assignment page. Introducing `Region` and a `Customer` → `CustomerLocation` → `ServiceVisit` hierarchy gives us a place to hang region data, and matches how service visits are actually generated (a customer's location is what's being visited, not the customer as a whole).

## What Changes

- Add a `Region` domain model (id, name).
- Add a `Customer` domain model (id, name) and a `CustomerLocation` domain model (id, customer_id, region_id, address, latitude, longitude); a customer has one or more locations.
- **BREAKING**: `ServiceVisit` no longer stores `customer_name`, `address`, `latitude`, `longitude` directly. It instead references a `CustomerLocation` via `customer_location_id`; customer name, address, coordinates, and region are read through that relation.
- Add a many-to-many relationship between `Employee` and `Region` (an employee can belong to more than one region), backed by an `employee_regions` join table.
- `GET /employees` and `GET /service-visits` (and the nested employee/visit data on `GET /assignments`) return region information (region name) alongside existing fields.
- The assignment page's employee, unassigned-visit, and assigned-visit cards each get a click-to-expand info box showing region and other extended detail (customer name/address for visits) not shown on the collapsed card.
- Extend the seed script to generate demo `Region`, `Customer`, and `CustomerLocation` data, and to create service visits from those locations instead of flat visit records; seeded employees get a region assigned too.

## Capabilities

### New Capabilities
- `regions`: `Region` domain model — a named geographic grouping referenced by employees and customer locations.
- `customers`: `Customer` and `CustomerLocation` domain models — a customer's serviceable locations, each in a region, from which service visits are generated.

### Modified Capabilities
- `employees`: employees can now belong to one or more regions (many-to-many), and the list-employees API returns each employee's regions.
- `service-visits`: visits are generated from a `CustomerLocation` rather than storing customer/location fields directly; the list-visits API returns customer and region information through that relation.
- `assignments`: the assignment page's employee/visit cards show region information and support expanding an info box with extended detail.

## Impact

- Backend: new `regions`, `customers`, `customer_locations`, and `employee_regions` (join) tables, a new Alembic migration altering `service_visits` (drop flat customer/location columns, add `customer_location_id`), updated Pydantic schemas and endpoint responses, updated seed script.
- Frontend: updated types/API client for the new nested region/customer fields, and new expandable info-box UI on each card in the three list sections.
- No new top-level API endpoints are required; region/customer/location data is exposed only through the existing employees/service-visits/assignments responses.
