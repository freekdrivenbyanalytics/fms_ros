## Why

We are building a field service planning application. Before any scheduling automation (route optimization, Timefold, maps) can be added, we need a proven core: a persisted domain model for employees, service visits, and assignments, exposed through an API and a minimal UI that lets a planner manually assign an unassigned visit to an employee. This first change establishes and proves that full stack (database → API → UI → assignment) so later changes can build automation on top of a working foundation.

## What Changes

- Add a PostgreSQL-backed domain model for `Employee`, `ServiceVisit`, and `Assignment`.
- Add a FastAPI backend (SQLAlchemy 2.x + Alembic migrations) exposing REST endpoints to list employees, list service visits (with status), and create/view assignments.
- Add a React + Vite + TypeScript frontend (Tailwind/shadcn) with a single page showing:
  - the list of employees
  - unassigned service visits
  - assigned service visits
- Support manually assigning an unassigned service visit to an employee with a chosen planned start time (planned end is derived from the visit's `duration_minutes`).
- Add Docker Compose for local PostgreSQL, with instructions to run backend and frontend locally.
- Explicitly out of scope for this change: route optimization, Timefold, maps/geocoding, traffic, recurring visits, employee skills, customer preferences, drag-and-drop UI.

## Capabilities

### New Capabilities
- `employees`: Employee domain model and read API (list employees with their working hours and location).
- `service-visits`: Service visit domain model and API (list visits, distinguish unassigned vs. assigned by status).
- `assignments`: Assignment domain model and API/UI flow to manually assign an unassigned service visit to an employee with a planned start time.

### Modified Capabilities
None — this is a greenfield project with no existing specs.

## Impact

- New backend service (Python/FastAPI) with a PostgreSQL database, new Alembic migrations, and a new SQLAlchemy schema (`employees`, `service_visits`, `assignments` tables).
- New frontend application (React/Vite/TypeScript) consuming the new REST API.
- New local dev tooling: `docker-compose.yml` for PostgreSQL.
- No existing code or systems are affected — this is the first change in the repository.
