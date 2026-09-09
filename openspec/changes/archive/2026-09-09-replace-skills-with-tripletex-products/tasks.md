## 1. Backend: data model and migration

- [x] 1.1 In `backend/app/models.py`, replace `Skill` (114-128) with `Product`: `id` (Tripletex's own id, not autoincrement), `number`, `name`, `delete_flag`.
- [x] 1.2 Rename `employee_skills` → `employee_products` and `contract_line_skills` → `contract_line_products` association tables; rename `Employee.skills` → `Employee.products` and `ContractLine.required_skills` → `ContractLine.required_products`.
- [x] 1.3 Add a new Alembic migration that drops `skills`, `employee_skills`, `contract_line_skills` and creates `products`, `employee_products`, `contract_line_products` (products keyed by Tripletex's own id, not autoincrement, mirroring how `Customer`/`CustomerLocation` are keyed).
- [x] 1.4 Add a `ProductSyncLog` table mirroring the existing `*SyncLog` pattern used by customer/location sync (`change_type` enum: CREATED/UPDATED/DELETED/RESTORED).

## 2. Backend: Tripletex product sync

- [x] 2.1 In `backend/app/tripletex.py`, add `get_products()` mirroring `get_customers()`/`get_delivery_addresses()`: page through `GET {base_url}/product` with `from`/`count`, filtering to TJN-numbered products client-side (a live call revealed the `number` query param filters by numeric id, not substring — see design.md's corrected decision).
- [x] 2.2 Add a scalar field map for Product (`id`, `number`, `name`) mirroring `_SCALAR_FIELD_MAP`.
- [x] 2.3 Add `sync_products(db)` mirroring `sync_customers`: upsert by Tripletex id, soft-delete locally present products no longer returned, restore ones that reappear, log to `ProductSyncLog`.
- [x] 2.4 Verify the real field names (`number`, `name`, `isInactive`) against an actual Tripletex sync call before considering this done. Verified live: 25 TJN-numbered products exist in this tenant, including all three the user specified (TJN10001, TJN10018, TJN10010) and TJN10001 matching the user's exact example ("Vaktmesteravtale 1-45").

## 3. Backend: API surface

- [x] 3.1 In `backend/app/main.py`, remove the `/skills` CRUD endpoints (list/create/update/delete) and the `Skill` import.
- [x] 3.2 Add `GET /products` (list, excluding soft-deleted by default) and `POST /products/sync` (triggers `sync_products`, mirrors `/customers/sync`'s error handling — 502 on failure).
- [x] 3.3 Rename `_lookup_regions_and_skills` to `_lookup_regions_and_products`; update its callers (employee create/update).
- [x] 3.4 Rename every `skill_ids`/`required_skill_ids` payload field to `product_ids`/`required_product_ids` across employee and contract-line create/update endpoints, and every `joinedload(...Employee.skills...)` / `joinedload(...ContractLine.required_skills...)` to the product equivalent (employee list, contract list, service-visit list, `/optimize/propose`, `ad_hoc_visits.py`'s free-slot search).
- [x] 3.5 In `backend/app/schemas.py`, remove `SkillOut`/`SkillCreate`/`SkillUpdate`; add `ProductOut` (id, number, name); rename `required_skills`/`skill_ids` fields on `ContractLineOut`/`ContractLineCreate`/`ContractLineUpdate`/`EmployeeOut`/`EmployeeCreate`/`EmployeeUpdate` to their product equivalents.
- [x] 3.6 In `backend/app/ad_hoc_visits.py`, rename `required_skill_ids`/`Employee.skills` references (lines 35, 39, 46, and the docstring at 94) to products.

## 4. Solver: constraint rename

- [x] 4.1 In `solver/app/domain.py`, rename `Employee.skill_ids` and `VisitAssignment.required_skill_ids` to `product_ids`/`required_product_ids`.
- [x] 4.2 In `solver/app/constraints.py`, rename `_missing_skills` to `_missing_products` and the `"Missing required skill"` constraint name to `"Missing required product"`; keep the subset-match logic unchanged.
- [x] 4.3 In `solver/app/schemas.py` and `backend/app/solver_client.py`, rename `skill_ids`/`required_skill_ids` payload fields to match. Also updated `solver/app/solve.py` (`_build_schedule`) and `solver/app/main.py` (warm-up fixture), which construct these objects from the request payload — not explicitly named in this task but required for the rename to be consistent end-to-end.

## 5. Frontend: Admin Portal

- [x] 5.1 Delete `frontend/src/admin-portal/SkillsView.tsx`.
- [x] 5.2 Add `frontend/src/admin-portal/ProductsView.tsx`: read-only list + detail (own fields, employees who hold it, contract lines that require it) with a "Refresh from Tripletex" button, mirroring the Customer Portal's Tripletex-refresh pattern.
- [x] 5.3 In `AdminPortalApp.tsx`, replace the "Skills" nav entry and `listSkills()` data loading with a "Products" entry and `listProducts()`.
- [x] 5.4 In `admin-portal/ContractsView.tsx`, replace the required-skills checkbox list (lines ~435-538: `skillIds`, `toggleSkill`) with a multi-select product dropdown (`<select multiple>`, still allowing more than one selection — only the control shape changes).

## 6. Frontend: other views

- [x] 6.1 In `employee-management/EmployeesView.tsx`, rename the skill checkbox list (lines ~116-208: `skillIds`, `toggle`) to reference products — same checkbox shape, per design.md's decision not to change this control's form.
- [x] 6.2 In `EmployeeManagementApp.tsx`, rename `listSkills()`/skills data loading to products.
- [x] 6.3 In `frontend/src/lib/listFilter.ts` and `components/ListFilterBar.tsx`, rename the skill filter dimension to product; update `EmployeeList.tsx`, `UnassignedVisitList.tsx`, `AssignedVisitList.tsx` accordingly.
- [x] 6.4 In `DayPlanningView.tsx` (lines ~92-97, 127-132), rename the employee-skills row-label badge and visit required-skills detail to products.
- [x] 6.5 In `customer-portal/ContractsView.tsx` (lines ~45-53) and `customer-portal/CustomerLocationsView.tsx` (lines ~54-55), rename the read-only `required_skills` badge display to products.
- [x] 6.6 In `frontend/src/types.ts`, remove `Skill`/`SkillCreateInput`/`SkillUpdateInput`; add `Product`/equivalents; rename embedded fields on `ContractLine`/`ContractLineCreateInput`/`ContractLineUpdateInput`/`Employee`/`EmployeeCreateInput`/`EmployeeUpdateInput`.
- [x] 6.7 In `frontend/src/api.ts`, remove `listSkills`/`createSkill`/`updateSkill`/`deleteSkill`; add `listProducts`/`syncProducts`.

Note: verified via `npx tsc --noEmit -p tsconfig.app.json`, not `-p .` — this project uses TS project references with an empty root `files: []`, so `-p .` silently typechecks nothing and reports a false "success." Flagging since earlier changes this session may have been "verified" with the misleading command.

## 7. Seed script

- [x] 7.1 In `backend/app/seed.py`, remove the `_get_or_create(db, Skill, name)` fixture block (lines ~43-46) and call `sync_products(db)` instead, alongside the existing `sync_customers`/`sync_customer_locations` calls.
- [x] 7.2 Replace employee fixtures' `"skills"` lists (lines ~51-79) with a random selection among the synced products whose number is TJN10001, TJN10018, or TJN10010 (`_random_products` helper).
- [x] 7.3 Replace contract line fixtures' `"required_skills"` lists (lines ~149-174) the same way.
- [x] 7.4 Update the final summary print (lines ~213-218) to report product counts instead of skill counts.

## 8. Verification

- [x] 8.1 Run the new migration against a copy of the current database; confirm `skills`/`employee_skills`/`contract_line_skills` are gone and `products`/`employee_products`/`contract_line_products` exist. Verified via a `pg_dump`/restore copy (`fms_ros_migration_test`), not the live database — also verified the downgrade path and a full from-scratch `0001`→`0013` migration chain.
- [x] 8.2 Trigger a product sync and confirm only TJN-numbered products are created locally, using the real Tripletex account this project already syncs customers from. 25 TJN products synced via the live `POST /products/sync` endpoint.
- [x] 8.3 Re-run the sync and confirm no duplicates are created (idempotent upsert), and that removing/reinstating a product in Tripletex soft-deletes/restores it locally. Re-sync held at 25 rows (no dupes); a locally-injected non-Tripletex product got soft-deleted on next sync; a locally soft-deleted real product got restored on next sync.
- [x] 8.4 Create a contract line via the API layer the product dropdown talks to, confirm selecting more than one product persists correctly. Created a line with 3 required products via `POST /contracts/{id}/lines`; all 3 came back correctly on the response.
- [x] 8.5 Confirm an employee lacking a visit's required product is correctly excluded from a proposed schedule (the renamed "Missing required product" constraint), using the same live-solver verification approach as `limit-solver-scheduling-window`. Verified both directions: unscheduled when no employee held the product, then scheduled to that employee once the product was granted.
- [x] 8.6 Run the updated seed script end-to-end and confirm employees and contract lines end up with a random mix of TJN10001/TJN10018/TJN10010. Ran against a fresh empty database; all 3 employees and all 4 contract lines got a non-empty random mix.
- [x] 8.7 Grep the codebase for remaining `skill`/`Skill` references outside historical migration files and archived OpenSpec changes, to confirm nothing was missed. Found and fixed one real leftover (`solver/verify_domain.py`, which imports directly from the renamed `app.domain`/`app.constraints`); left `solver/discovery_spike2.py` alone since it's a fully self-contained old exploration script with no import from production code.
