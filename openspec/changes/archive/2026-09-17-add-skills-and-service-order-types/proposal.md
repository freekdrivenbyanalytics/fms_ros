## Why

Employee-to-visit qualification is currently checked by "does the employee hold the exact products the contract line requires" — a coarse proxy, since a product (a billable Tripletex catalog line) isn't really the right unit for "can this person do this kind of work." This change introduces `Skill` as the real qualification currency (an employee has skills; a product requires skills), and `ServiceOrderType` as a classification of what kind of work a product represents — both new, local-only concepts that don't exist in Tripletex or Resco. fms_ros had a `Skill` concept once before (dropped when products were introduced, per `openspec/changes/archive/*replace-skills-with-products*` history) — this reintroduces it deliberately as an attribute of products and employees together, not a replacement for products.

## What Changes

- Add `Skill` (name, soft-delete flag) as a new local-only entity, with full CRUD in the Admin Portal. A skill can be required by zero or more products, and held by zero or more employees.
- Add `ServiceOrderType` (name, soft-delete flag) as a new local-only entity, with full CRUD in the Admin Portal. Every product has exactly one service order type, classifying the kind of work it represents.
- **BREAKING**: Employee qualification moves from `Employee.products` to `Employee.skills`. An employee no longer directly holds products; instead, an employee qualifies for a contract line's visit when they hold every skill required by every product that contract line requires (skills are the qualification currency, products stay the demand-side unit contract lines specify). `Employee.products` and its association table are removed — Employee Management's employee form and detail view show skills instead of products.
- The Timefold solver's qualification hard constraint changes from "employee holds every required product" to "employee holds every skill those required products require" — same hard-constraint shape, different underlying check.
- The Manual Assignment screen's unassigned/assigned visit lists show each visit's required skills (derived from its required products), not just its required products.
- Demo data: reuse 4 existing, already-synced Tripletex products rather than creating new ones — TJN10001/TJN10002/TJN10003 get service order type "Generelle vaktmestertjenester" and skill "Inspeksjon (vaktmester)"; TJN10010 (Tripletex's own "Vintervedlikehold liten") gets service order type "Vaktmestertjenester (vinter)" and skills "Inspeksjon (vaktmester)" + "Snømåking". The ~40 contract lines currently requiring TJN10004 (a plain, unrelated product not part of this scheme) are reassigned to require TJN10010 instead. 2 new skills and 2 new service order types are created and wired to these 4 products and to the 3 active employees exactly as specified in tasks.md.

## Capabilities

### New Capabilities
- `skills`: a skill is a named qualification; products require skills, employees hold skills.
- `service-order-types`: a service order type classifies what kind of work a product represents; every product has exactly one.

### Modified Capabilities
- `products`: a product gains a required-skills association and a service order type.
- `employees`: an employee gains a skills association, replacing its products association.
- `employee-management`: the employee list/detail/create/update views show and edit skills instead of products.
- `admin-portal`: gains Skills and Service Order Types views (list/detail/CRUD); the Products view (from `add-master-data-crud`) gains skill and service-order-type fields.
- `ad-hoc-visits`: free-slot qualification checks the employee's skills against the contract line's required products' skills, instead of checking products directly.
- `route-optimization`: the solver's qualification hard constraint checks skills instead of products.
- `service-visits`: the service visit list API additionally returns each visit's required skills (derived from its contract line's required products).

## Impact

- `backend/app/models.py`: new `Skill`, `ServiceOrderType` models; new `product_skills` (Product↔Skill) and `employee_skills` (Employee↔Skill) association tables; `service_order_type_id` FK on `Product`; `employee_products` association table and `Employee.products` relationship removed.
- `backend/app/schemas.py`, `backend/app/main.py`: new CRUD schemas/endpoints for Skill and ServiceOrderType; `ProductOut`/`ProductCreate`/`ProductUpdate` (from `add-master-data-crud`) gain `skill_ids`/`service_order_type_id`; `EmployeeOut`/`EmployeeCreate`/`EmployeeUpdate` swap `product_ids` for `skill_ids`; `ServiceVisitOut` gains derived `required_skills`.
- `backend/app/ad_hoc_visits.py`: `_qualifying_employees` checks skills instead of products.
- `solver/app/domain.py`, `solver/app/constraints.py`, `backend/app/solver_client.py`: `Employee.product_ids`/`VisitAssignment.required_product_ids` become skill-based (`employee_skill_ids`/`required_skill_ids`); the "Missing required product" constraint becomes "Missing required skill".
- `frontend/src/employee-management/`, `frontend/src/admin-portal/`: employee form/detail show skills instead of products; new `SkillsView.tsx`/`ServiceOrderTypesView.tsx`; Products view (from `add-master-data-crud`) gains skill/service-order-type fields; Manual Assignment's visit cards show required skills.
- `frontend/src/api.ts`, `frontend/src/types.ts`: new Skill/ServiceOrderType CRUD client functions and types; `Employee`/`Product`/`ServiceVisit` types updated.
- A one-off demo-data script (not permanent tooling, matching the pattern already used for Tripletex contact seeding) creates the 2 skills and 2 service order types, sets skill/service-order-type associations on the 4 existing products (TJN10001/10002/10003/10010), reassigns the ~40 TJN10004 contract lines to TJN10010, and sets the 3 active employees' skills.

**Depends on `add-master-data-crud`**: setting a product's `skill_ids`/`service_order_type_id` goes through that change's `PATCH /products` endpoint (extended by task 4.1 to also persist these two local-only fields alongside the existing Tripletex-facing ones). This change's demo-data task cannot run until that capability exists; the rest of this change (Skill/ServiceOrderType entities, the qualification refactor, the solver) does not depend on it and could be built independently.
