## Context

Greenfield repository — no existing code, backend, or frontend. See proposal.md - Why for motivation. Confirmed stack: Python + FastAPI backend, SQLAlchemy 2.x ORM, Alembic migrations, PostgreSQL, React + Vite + TypeScript frontend with Tailwind/shadcn, Docker Compose for local Postgres.

## Goals / Non-Goals

**Goals:**
- Stand up a working vertical slice: Postgres schema → SQLAlchemy models → FastAPI REST endpoints → React UI → manual assignment action.
- Keep the domain model exactly as specified (three entities, no extra fields) so later changes add to a known-good baseline.

**Non-Goals:**
- No authentication/authorization — single implicit planner user for this change.
- No optimistic concurrency handling beyond the single "already assigned" check in specs/assignments.
- No pagination, filtering, or search on lists — all employees/visits are returned in full (acceptable at this scale).
- No seed/demo data pipeline beyond a minimal fixture for manual testing.

## Decisions

- **Repo layout**: two top-level dirs, `backend/` (FastAPI app) and `frontend/` (Vite React app), plus a root `docker-compose.yml` for Postgres. Keeps the two stacks independently runnable, matches the confirmed tooling (Alembic lives under `backend/`).
- **Assignment as its own table, not a column on ServiceVisit**: matches the given schema (`Assignments` has its own id-less composite of `service_visit_id`, `employee_id`, `planned_start`, `planned_end`) and keeps a visit's "unassigned" state as "no row in `assignments`" rather than a set of nullable columns. `ServiceVisit.status` is stored as a persisted column, not derived on every read, because `status` is explicitly listed as a field on the service visit entity — it is recomputed and written whenever an assignment is created (`unassigned` → `assigned`) so it always matches whether an assignment row exists.
- **planned_end computed server-side**: the API accepts only `planned_start` from the client; `planned_end = planned_start + duration_minutes` is computed in the backend when the assignment is created, so the derivation lives in one place and can't drift from the visit's `duration_minutes`.
- **One-shot assignment creation, no update/unassign endpoint**: the proposal only asks for manual assignment of unassigned visits, not reassignment or un-assignment. Adding those now would be speculative; explicitly left out per "Do not implement... drag and drop" and the minimal-scope instruction.
- **UI as a single page, no routing library**: one screen (employees / unassigned visits / assigned visits + an assign action) doesn't need client-side routing yet.

## Risks / Trade-offs

- [No auth] → Acceptable for this internal, first-change prototype; must be revisited before any real deployment.
- [Status stored redundantly with assignment existence] → Mitigated by only ever writing `status` inside the same transaction that creates the assignment, so the two never disagree in normal operation.
- [No update/delete on assignments] → If a planner mis-assigns a visit there is no corrective flow yet; acceptable since this change's purpose is to prove the flow works end-to-end, not to be feature-complete.
