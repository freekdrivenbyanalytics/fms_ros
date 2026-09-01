## Why

Skills are the last read-only, name-only master-data entity still sitting in the customer-facing Customer Portal. Following the same move already made for Regions, Skills belongs in the Admin Portal — internal masterdata management shouldn't live in a portal meant for browsing customer-facing data — and while moving it, it should get the same full CRUD Regions just got, rather than staying a static, seed-only lookup table.

## What Changes

- **BREAKING**: Remove the Skills list/detail view from the Customer Portal. Skills are no longer visible or manageable there.
- Add full CRUD (create, update, soft-delete) for skills from the Admin Portal, alongside the existing Regions management: name only. Soft-delete follows the existing `delete_flag` pattern used elsewhere.
- The Admin Portal's Skill detail view shows read-only cross-references: the employees who hold that skill and the contract lines that require it (the same two associations the Customer Portal's Skill detail showed piecemeal — contract lines only, since Employees had already left the Customer Portal in an earlier change — now shown together in one place since the Admin Portal already has both employees and contracts loaded).
- No change to how a skill gets attached to an employee or a contract line: those stay exactly as they are today, edited from the employee's own form (Employee Management) or the contract line's own form (Customer Portal's Contracts view), not duplicated into the Admin Portal.

## Capabilities

### Modified Capabilities
- `skills`: data model gains a soft-delete flag; adds create/update/soft-delete requirements and a "deleted skills are hidden by default" requirement.
- `customer-portal`: remove Skills from the portal's entity list, list views, detail views, and every requirement/scenario that names it.
- `admin-portal`: add Skill list/detail views and CRUD, alongside the existing Region management, following the same shape.

## Impact

- Backend: `Skill` gains `delete_flag`; new migration; new schemas/endpoints for skill CRUD; `GET /skills` excludes soft-deleted skills by default.
- Frontend: new `frontend/src/admin-portal/SkillsView.tsx` (list/detail/CRUD, mirroring `RegionsView.tsx`'s shape) added to the existing Admin Portal app; `frontend/src/customer-portal/SkillsView.tsx` and its Customer Portal wiring removed.
- No change to the route optimizer, to how contract lines or employees reference skills, or to Regions.
