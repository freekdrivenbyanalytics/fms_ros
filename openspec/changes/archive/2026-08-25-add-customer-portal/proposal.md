## Why

Today the only user-facing surface on top of the shared backend/database is the internal Planning application (Manual Assignment + Day Planning), used by a planner assigning visits to employees. There is no way for a business user responsible for master data (customers, their locations, contracts, skills, regions, employees) to browse that data without going through the API directly. Establishing a second, clearly separate frontend area — the Customer Portal — validates that the existing domain model and backend can serve more than one user experience, and gives master-data administrators a simple way to see what's already in the system before any editing, sync, or integration capability is built on top.

## What Changes

- Add a new, clearly separate top-level area in the frontend — the Customer Portal — reachable from a landing entry point distinct from the Planning application's own navigation. It has no shared header/nav with Manual Assignment or Day Planning, though both live in the same frontend project and talk to the same backend.
- The Customer Portal shows a list view for each of six master-data entities: Employees, Customers, Customer Locations, Contracts, Skills, Regions.
- Opening an item from a list shows a detail view with that item's own fields plus its relationships to other entities (e.g. opening a Customer shows its Customer Locations; opening a Region shows the Employees scoped to it and the Customer Locations in it; opening a Skill shows the Employees who have it and the Contracts that require it).
- The portal is entirely read-only: no create, edit, or delete action anywhere in it.
- Backend: add plain list-read endpoints for the three entities not yet independently exposed (`GET /customers`, `GET /customer-locations`, `GET /contracts`; `GET /regions` and `GET /skills` are also new, `GET /employees` already exists and is reused as-is). Each reuses the existing Pydantic output schemas (`CustomerOut`, `CustomerLocationOut`, `ContractOut`, `RegionOut`, `SkillOut`) already defined in `backend/app/schemas.py` — no new schemas, no domain model changes, no changes to any existing endpoint.
- Out of scope for this change (explicitly deferred): creating/editing/deleting master data, authentication or customer self-service login, different user roles, Resco/ERP/Timefold integration, and any synchronization logic. The portal assumes an administrator is already using it; no login screen is added.

## Capabilities

### New Capabilities
- `customer-portal`: A read-only, browse-only view of the six master-data entities (Employees, Customers, Customer Locations, Contracts, Skills, Regions) and their relationships, in a frontend area kept clearly separate from the Planning application.

### Modified Capabilities
None — `GET /employees` is reused unmodified; the new `GET /customers`, `/customer-locations`, `/contracts`, `/regions`, `/skills` endpoints are net-new API surface with no effect on any existing capability's documented behavior (assignments, service-visits, employees, customers, customer-locations, contracts, skills, regions all keep their current persistence/behavior guarantees unchanged).

## Impact

- **Affected code**: `backend/app/main.py` (5 new `GET` list endpoints, reusing existing schemas — no new Pydantic models, no model/migration changes); `frontend/src/` — a new top-level Customer Portal area (new components, a landing entry point separate from the Planning app's nav) and a few new `frontend/src/api.ts` functions for the new endpoints.
- **Affected systems**: Backend gains new read-only routes; frontend gains a new top-level area. No database schema changes, no new dependencies, no authentication changes.
- **Dependencies**: None planned.
