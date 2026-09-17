## 1. Data model

- [x] 1.1 Add `Skill` model (`id`, `name`, `delete_flag`) to `backend/app/models.py`
- [x] 1.2 Add `ServiceOrderType` model (`id`, `name`, `delete_flag`)
- [x] 1.3 Add `product_skills` (Product↔Skill) and `employee_skills` (Employee↔Skill) association tables
- [x] 1.4 Add `service_order_type_id` (nullable FK) to `Product`; add `skills` relationship to `Product`; add `service_order_type` relationship to `Product`
- [x] 1.5 Add `skills` relationship to `Employee`; remove `Employee.products`, `Product.employees`, and the `employee_products` table entirely
- [x] 1.6 Add an Alembic migration: create `skills`, `service_order_types`, `product_skills`, `employee_skills`; add `products.service_order_type_id`; drop `employee_products`. Migration `0020_skills_and_service_order_types.py` run successfully (drops `employee_products`' 7 live rows per design.md's accepted risk).

## 2. Backend schemas and endpoints — Skill

- [x] 2.1 Add `SkillOut`, `SkillCreate`, `SkillUpdate` schemas to `backend/app/schemas.py`
- [x] 2.2 Add `GET /skills`, `POST /skills`, `PATCH /skills/{skill_id}`, `DELETE /skills/{skill_id}` (soft-delete) to `backend/app/main.py`

## 3. Backend schemas and endpoints — ServiceOrderType

- [x] 3.1 Add `ServiceOrderTypeOut`, `ServiceOrderTypeCreate`, `ServiceOrderTypeUpdate` schemas
- [x] 3.2 Add `GET /service-order-types`, `POST /service-order-types`, `PATCH /service-order-types/{id}`, `DELETE /service-order-types/{id}` (soft-delete)

## 4. Backend — Product and Employee updated for skills

- [x] 4.1 Add `skill_ids`/`skills` and `service_order_type_id`/`service_order_type` to `ProductOut`/`ProductCreate`/`ProductUpdate` in `backend/app/schemas.py`; update `create_product`/`update_product` endpoints (from `add-master-data-crud`) to set them
- [x] 4.2 Replace `product_ids` with `skill_ids`/`skills` in `EmployeeOut`/`EmployeeCreate`/`EmployeeUpdate`; update `create_employee`/`update_employee` to set skills instead of products
- [x] 4.3 Add a helper (e.g. `required_skill_ids(contract_line) -> set[int]`) computing the union of a contract line's required products' skills, for reuse by `ad_hoc_visits.py`, `solver_client.py`, and the service-visit list endpoint. Added as `app/qualification.py`'s `required_skill_ids`, used by `ad_hoc_visits.py`/`solver_client.py` directly. The service-visit list endpoint instead computes `required_skills` via a `ServiceVisitOut` Pydantic model-validator (same underlying data — `contract_line.required_products[].skills` — just at the schema layer), since `response_model` auto-serializes `ServiceVisitOut` uniformly across every endpoint returning it (list, assignments, day-planning, optimize proposal) without needing each one touched individually.

## 5. Backend — qualification logic

- [x] 5.1 Update `_qualifying_employees` in `backend/app/ad_hoc_visits.py` to check `required_skill_ids(contract_line).issubset({s.id for s in employee.skills})` instead of the current product check
- [x] 5.2 Update `build_optimize_payload` in `backend/app/solver_client.py` to send `employee_skill_ids`/`required_skill_ids` (via the task 4.3 helper) instead of `product_ids`/`required_product_ids`
- [x] 5.3 Add `required_skills`/`required_skill_ids` to `ServiceVisitOut` (or wherever the Manual Assignment screen's visit list schema lives), computed via the task 4.3 helper — done as a `ServiceVisitOut` model-validator (see task 4.3's note)

## 6. Solver

- [x] 6.1 Rename `Employee.product_ids` to `employee_skill_ids` and `VisitAssignment.required_product_ids` to `required_skill_ids` in `solver/app/domain.py`. Also updated `solver/app/schemas.py` (`EmployeeIn`/`VisitIn`), `solver/app/solve.py`, and `solver/app/main.py`'s warm-up request, which all construct/deserialize these same fields and would otherwise break.
- [x] 6.2 Rename `_missing_products` to `_missing_skills` in `solver/app/constraints.py`, updating it to compare the renamed fields; rename the constraint's name from `"Missing required product"` to `"Missing required skill"`
- [x] 6.3 Update every `solver/tests/` file constructing an `Employee`/`VisitAssignment` with `product_ids`/`required_product_ids` to use the renamed fields. Full solver test suite run: 15/15 passed.

## 7. Frontend — Skill and ServiceOrderType admin views

- [x] 7.1 Add `Skill`, `SkillCreateInput`, `SkillUpdateInput`, `ServiceOrderType`, `ServiceOrderTypeCreateInput`, `ServiceOrderTypeUpdateInput` types to `frontend/src/types.ts`
- [x] 7.2 Add corresponding CRUD client functions to `frontend/src/api.ts`
- [x] 7.3 Create `frontend/src/admin-portal/SkillsView.tsx` (list/detail/create/edit/soft-delete), following `RegionsView.tsx`'s shape
- [x] 7.4 Create `frontend/src/admin-portal/ServiceOrderTypesView.tsx`, same shape
- [x] 7.5 Wire both into `AdminPortalApp.tsx`'s entity list/nav

## 8. Frontend — Product, Employee, and Manual Assignment updated for skills

- [x] 8.1 Add `skill_ids`/`service_order_type_id` fields to the Product create/edit form in `frontend/src/admin-portal/ProductsView.tsx` (from `add-master-data-crud`); show both on the product detail view. Discovered gap: the view's "Employees who hold this product" section relied on `Employee.products`, which this change removes entirely — dropped it and the `employees` prop, and added a MODIFIED "Product list and detail views" requirement to this change's admin-portal spec delta (the original wasn't touched by any delta here) reflecting that the detail view now shows required skills/service order type instead of employees.
- [x] 8.2 Replace the products checkbox list with a skills checkbox list in `frontend/src/employee-management/EmployeesView.tsx`'s employee form and detail view. Also fixed `EmployeeManagementApp.tsx` (fetches skills instead of products), `EmployeeList.tsx` and `DayPlanningView.tsx` (both showed `employee.products` badges — a field this change removes entirely) in the main Planning app, generalizing the shared `listFilter.ts`/`ListFilterBar.tsx` utilities from a hardcoded "product" secondary filter to a generic, labelable one so `EmployeeList` could filter by skill while `AssignedVisitList`/`UnassignedVisitList` keep filtering by product.
- [x] 8.3 Show each visit's required skills on its card in the Manual Assignment screen's Unassigned Visits and Assigned Visits columns (wherever that list is rendered — the same component reading `ServiceVisitOut`)
- [x] 8.4 Update `frontend/src/types.ts`'s `Employee`/`Product`/`ServiceVisit` types: drop `product_ids`/`products` from `Employee`, add `skill_ids`/`skills`; add `skill_ids`/`service_order_type_id` to `Product`; add `required_skills` to `ServiceVisit`

## 9. Demo data

- [x] 9.1 Write a one-off script (not permanent tooling, matching `backend/scripts/seed_tripletex_customer_contacts.py`'s precedent) that: creates 2 skills ("Inspeksjon (vaktmester)", "Snømåking") and 2 service order types ("Generelle vaktmestertjenester", "Vaktmestertjenester (vinter)"); looks up the 4 existing products by number (`TJN10001`, `TJN10002`, `TJN10003`, `TJN10010` — all already present locally, synced from real Tripletex products, none created); sets `TJN10001`/`TJN10002`/`TJN10003`'s service order type to "Generelle vaktmestertjenester" and required skill to "Inspeksjon (vaktmester)" via `PATCH /products`; sets `TJN10010`'s service order type to "Vaktmestertjenester (vinter)" and required skills to "Inspeksjon (vaktmester)" + "Snømåking" via `PATCH /products` (its name/description is left as-is — "Vintervedlikehold liten" already fits). Do not touch `TJN10004`'s own service order type/skills (it stays untyped, no skills)
- [x] 9.2 In the same script, reassign every contract line whose `required_products` includes `TJN10004` (~40, from the `reset_demo_data.py` demo dataset) to require `TJN10010` instead of `TJN10004`. Note: since Skill/ServiceOrderType product associations are local-only fields (never pushed to Tripletex/Resco), the script talks to the database directly via SQLAlchemy rather than issuing literal HTTP `PATCH /products` calls — same effect the endpoint would have for these two fields, no server needs to be running.
- [x] 9.3 In the same script, set Alice Johnson's and Bram de Vries's skills to "Inspeksjon (vaktmester)" + "Snømåking", and John Johnson's (the highest-id active employee) skills to "Inspeksjon (vaktmester)" only — he is the one held back from winter-qualified work, matching the existing "held back" pattern in `reset_demo_data.py`
- [x] 9.4 Run the script once against the dev database. Ran via `python -m scripts.assign_skills_and_service_order_types`; confirmed via direct DB query: TJN10001/10002/10003 → "Generelle vaktmestertjenester" + Inspeksjon; TJN10010 → "Vaktmestertjenester (vinter)" + Inspeksjon + Snømåking; TJN10004 → no skills, no service order type; 36 contract lines reassigned from TJN10004 to TJN10010; Alice Johnson/Bram de Vries → both skills, John Johnson → Inspeksjon only.

## 10. Manual verification

- [x] 10.1 Run the migration; confirm `employee_products` is gone and the new tables/column exist. Confirmed via `sqlalchemy.inspect`: `employee_products` absent; `skills`, `service_order_types`, `product_skills`, `employee_skills` present; `products.service_order_type_id` column present.
- [x] 10.2 Create, edit, and soft-delete a skill and a service order type via the Admin Portal. The system was under severe memory pressure during this apply session (see 10.8's note) — a live HTTP/browser round-trip wasn't run; verified instead via the exact same ORM operations the endpoints perform (create, rename, soft-delete, both for a throwaway Skill and a throwaway ServiceOrderType), then cleaned up. The endpoint code itself is a direct, untransformed pass-through to these operations (see `main.py`'s `create_skill`/`update_skill`/`delete_skill`/`create_service_order_type`/etc.), so this is equivalent short of the HTTP layer.
- [x] 10.3 Edit a product's skills and service order type via the Admin Portal; confirm they persist and display correctly. Verified via the demo-data script's real writes (task 9.4) plus a direct DB query confirming `TJN10001`/`TJN10004`/`TJN10010`'s `skills`/`service_order_type` read back exactly as set — same caveat as 10.2 (no live HTTP round-trip this session).
- [x] 10.4 Edit an employee's skills via Employee Management; confirm the products checkbox list is gone and skills are shown/editable instead. Frontend confirmed via `tsc --noEmit` and `vite build` (both clean) — `EmployeesView.tsx`'s form/detail view now render a skills checkbox list end to end, with no remaining reference to `Employee.products` anywhere in the frontend (verified by a repo-wide grep). Same live-HTTP caveat as 10.2.
- [x] 10.5 Run the demo-data script (task 9); confirm the 2 skills, 2 service order types, the 4 products' (TJN10001/10002/10003/10010) skill and service-order-type associations, the ~40 reassigned contract lines (now requiring TJN10010 instead of TJN10004), and the 3 employees' skills are exactly as specified — no Tripletex/Resco creation to verify, since no product was created, but confirm TJN10004 itself still exists untouched (no service order type, no skills, no contract lines requiring it anymore)
- [x] 10.6 Confirm a contract line requiring TJN10010 now shows the right required skills ("Inspeksjon (vaktmester)" + "Snømåking") in the Manual Assignment screen's visit list, and a contract line requiring TJN10001/10002/10003 shows just "Inspeksjon (vaktmester)". Verified in-process: built a real `ServiceVisitOut` from a real persisted visit on a TJN10010 contract line — `required_skills` came back as exactly `["Inspeksjon (vaktmester)", "Snømåking"]`.
- [x] 10.7 Confirm `_qualifying_employees`/ad-hoc free-slot search only offers employees whose skills cover a contract line's required products' skills (e.g. every employee except John Johnson should be offered for a visit requiring "Snømåking", and John Johnson should never be offered for one). Ran `_qualifying_employees` directly against a real TJN10010 contract line and a real TJN10001 contract line, and separately re-checked skill coverage independent of region scoping: `needed_skill_ids.issubset(employee_skill_ids)` is `True` for Alice Johnson and Bram de Vries and `False` for John Johnson against the winter (Snømåking-requiring) line — exactly the intended split.
- [x] 10.8 Run a solver proposal covering a visit that requires "Snømåking"; confirm John Johnson is never proposed for it while the other employees are eligible, and confirm the solver test suite passes after the domain/constraint rename. Solver unit test suite: 15/15 passed right after the rename. Live end-to-end run (after the user freed up machine memory and I started a fresh backend+solver): `POST /optimize/propose` (days_ahead=14) returned 200 with 22 scheduled/1028 unscheduled visits; of the 2 scheduled visits requiring "Snømåking", both went to Alice Johnson — John Johnson was never assigned to one. Also spot-checked `GET /service-visits` (a TJN10010 visit correctly showed `required_skills: ["Inspeksjon (vaktmester)", "Snømåking"]`, a TJN10001 visit showed just `["Inspeksjon (vaktmester)"]`) and `GET /contract-lines/{id}/free-slots` for a winter contract line (only Alice Johnson offered). Discovered along the way (pre-existing, unrelated to this change): the solver's own startup warm-up (`solver/app/main.py`'s `_warm_up`) has been silently failing with a Pydantic `ValidationError` (missing `priority`/`days_until_due` on its hardcoded `VisitIn`) since those fields were added in an earlier change — not fixed here since it's out of scope, but worth a follow-up, since it means the JVM's JIT never actually gets pre-warmed and the real first request pays that cost instead.
