## 1. Backend data model & migration

- [x] 1.1 In `backend/app/models.py`: add `delete_flag` (Boolean, default False, server_default "false") to `Skill`.
- [x] 1.2 New Alembic migration `0010_skill_delete_flag.py`: add `skills.delete_flag` (Boolean, `server_default=false`). Purely additive — no truncation, no backfill. Write a `downgrade()` that drops the column.
- [x] 1.3 Run `alembic upgrade head`, then `alembic downgrade 0009`, then `alembic upgrade head` again to confirm both directions work cleanly against the running Postgres container.

## 2. Backend API

- [x] 2.1 Add `SkillCreate` (name) and `SkillUpdate` (name) schemas in `backend/app/schemas.py`; `SkillOut` already exists and needs no field changes.
- [x] 2.2 Add `POST /skills`, `PATCH /skills/{id}`, `DELETE /skills/{id}` (soft) in `backend/app/main.py`; update `GET /skills` to exclude `delete_flag=True` by default.
- [x] 2.3 Verify via API: creating a skill with a name works; updating a skill's name works; soft-deleting a skill excludes it from `GET /skills` while leaving referencing employees/contract lines unaffected.

## 3. Frontend: shared types and API client

- [x] 3.1 Update `frontend/src/types.ts`: no change needed to `Skill` itself (already `{id, name}`); add `SkillCreateInput`/`SkillUpdateInput`.
- [x] 3.2 Add `createSkill`, `updateSkill`, `deleteSkill` to `frontend/src/api.ts`, following the existing `createRegion`/`updateRegion`/`deleteRegion` pattern (manual 204 handling for delete).

## 4. Frontend: Admin Portal Skills view

- [x] 4.1 Create `frontend/src/admin-portal/SkillsView.tsx`, mirroring `RegionsView.tsx`'s shape: list view (shared `ListTable`) and detail view (shared `DetailField`) showing a skill's name, the employees who hold it (read-only, client-side filtered from already-fetched employees), and the contract lines that require it (read-only, client-side filtered from already-fetched contracts).
- [x] 4.2 Implement skill CRUD in `SkillsView.tsx`: create (name only), update (name), and soft-delete — no map/geo-shape involved, simpler than `RegionsView.tsx`.
- [x] 4.3 Wire `SkillsView` into `AdminPortalApp.tsx`: fetch `listContracts()` alongside the existing regions/employees/customerLocations fetches (needed for the "contract lines that require it" cross-reference), add a nav/section switch between Regions and Skills (mirroring how `CustomerPortalApp.tsx` switches between its entity views).

## 5. Frontend: remove Skills from the Customer Portal

- [x] 5.1 Delete `frontend/src/customer-portal/SkillsView.tsx` and remove the Skills list/detail route and nav entry from `CustomerPortalApp.tsx`.
- [x] 5.2 Remove any now-unused `skills` fetching/state from `CustomerPortalApp.tsx` (check `ContractsView`/`ContractLineForm` still needs a `skills` list for the required-skills checkboxes when creating/editing a contract line — keep fetching skills for that if so, just remove the standalone Skills view and its nav entry).

## 6. End-to-end verification

- [x] 6.1 Run `tsc -b` and confirm the frontend type-checks cleanly.
- [x] 6.2 Launch frontend + backend and manually confirm in the browser: the Admin Portal shows both Regions and Skills management; skill create/update/soft-delete work end-to-end; a skill's detail view shows the correct read-only employee/contract-line cross-references; the Customer Portal no longer shows Skills anywhere (nav, lists), while Contract Line create/edit still shows skill checkboxes correctly.
- [x] 6.3 Confirm `openspec validate --strict` passes for the change before archiving.
