## 1. Project scaffolding

- [x] 1.1 Create `backend/` (FastAPI app skeleton) and `frontend/` (Vite + React + TypeScript app skeleton) directories at the repo root
- [x] 1.2 Add `docker-compose.yml` at the repo root running a PostgreSQL service for local development
- [x] 1.3 Add backend dependency manifest (FastAPI, SQLAlchemy 2.x, Alembic, psycopg driver, uvicorn) and a `.env`/settings mechanism for the database URL
- [x] 1.4 Add frontend dependency manifest (React, Vite, TypeScript, Tailwind or shadcn/ui) and base app shell
- [x] 1.5 Document local run steps (start Postgres via Docker Compose, run backend, run frontend) in a README

## 2. Database & domain model

- [x] 2.1 Define SQLAlchemy 2.x model `Employee` (id, name, work_start, work_end, latitude, longitude)
- [x] 2.2 Define SQLAlchemy 2.x model `ServiceVisit` (id, customer_name, address, latitude, longitude, duration_minutes, requested_date, status)
- [x] 2.3 Define SQLAlchemy 2.x model `Assignment` (service_visit_id, employee_id, planned_start, planned_end) with foreign keys to `ServiceVisit` and `Employee`
- [x] 2.4 Initialize Alembic and create the initial migration creating the `employees`, `service_visits`, and `assignments` tables
- [x] 2.5 Add a minimal seed script/fixture that inserts a handful of employees and service visits for manual testing

## 3. Backend API

- [x] 3.1 Implement `GET /employees` returning all employees (per specs/employees: List employees)
- [x] 3.2 Implement `GET /service-visits` returning all service visits with their status (per specs/service-visits: List service visits by assignment status)
- [x] 3.3 Implement `POST /assignments` accepting `service_visit_id`, `employee_id`, `planned_start`; compute `planned_end` from the visit's `duration_minutes`, create the assignment, and set the visit's status to `assigned` (per specs/assignments: Manually assign an unassigned visit)
- [x] 3.4 Reject `POST /assignments` with an error response when the target visit's status is already `assigned` (per specs/assignments: Prevent double assignment)
- [x] 3.5 Implement `GET /assignments` (or include assignment details on assigned visits) so the UI can show assigned visits with their planned start/end and assigned employee

## 4. Frontend

- [x] 4.1 Build API client functions for listing employees, listing service visits, and creating an assignment
- [x] 4.2 Build the assignment page layout with three sections: employees, unassigned service visits, assigned service visits (per specs/assignments: View employees and visits for assignment)
- [x] 4.3 Add an "assign" action on an unassigned visit that lets the user pick an employee and a planned start time, then calls `POST /assignments`
- [x] 4.4 On successful assignment, move the visit from the unassigned list to the assigned list without a full page reload (refetch or local state update)
- [x] 4.5 Surface a visible error message if assignment creation fails (e.g., visit already assigned)

## 5. End-to-end verification

- [x] 5.1 Run backend against Dockerized Postgres, apply the Alembic migration, and confirm the schema matches the domain model
- [x] 5.2 Run the seed script and verify `GET /employees` and `GET /service-visits` return the expected data
- [x] 5.3 Run the frontend against the backend and manually verify the full flow: view employees and unassigned visits, assign a visit to an employee with a planned start time, and confirm it appears in the assigned list with the correct planned_end
- [x] 5.4 Manually verify that attempting to assign an already-assigned visit is rejected
