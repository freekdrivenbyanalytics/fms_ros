## Why

Skills today are a locally-owned, hand-maintained lookup (create/rename/soft-delete via the Admin Portal) used to qualify employees for contract-line requirements. The business wants Tripletex — already the master for customers and customer locations — to be the master for this qualification concept too, sourced from Tripletex's own product catalog (specifically the subset of products whose number starts with "TJN", e.g. "TJN10001 Vaktmesteravtale 1-45"). Locally-owned skills and Tripletex-synced products would otherwise be two competing, overlapping ways to express the same qualification concept, so skills are retired in favor of products rather than the two coexisting.

## What Changes

- **New**: a `products` capability, synced from Tripletex on demand (mirroring the existing customer sync pattern: upsert by Tripletex's own id, soft-delete ones no longer returned, restore ones that reappear), scoped to only products whose number starts with "TJN". Products are read-only locally — Tripletex is the sole master, with no local create/rename/delete.
- **Removed**: the `skills` capability entirely — the Skill data model, its CRUD, and its Admin Portal UI (list, detail, create/update/soft-delete) are all retired, replaced by the read-only Products view described below.
- Every place that referenced skills now references products instead, with the same multi-select shape as before (an employee can hold multiple products; a contract line can require multiple products — see below): `Employee.skills` → `Employee.products`, `ContractLine.required_skills` → `ContractLine.required_products`, the route optimizer's "Missing required skill" hard constraint → "Missing required product", the Planning app's region/skill filters → region/product filters, the day planning chart's skill badges → product badges, and the Admin/Customer Portal's read-only "required skills" displays → "required products".
- The Admin Portal's Contract Line form's required-skills checkbox list becomes a multi-select dropdown of products (a contract line can still require more than one product — only the control's shape changes, not the underlying multiplicity).
- The Admin Portal's Skills nav entry is replaced by a read-only "Products" view (list + detail, showing which employees hold a product and which contract lines require it — the same cross-reference display skills had) with a "Refresh from Tripletex" sync trigger, mirroring the Customer Portal's existing Tripletex refresh pattern.
- The Employee form's skill multi-select (checkboxes) becomes a product multi-select in the same shape — a control-content swap, not a control-shape change, since the user's request only called out the contract-line control's shape changing to a dropdown.
- The seed script's locally-fabricated skill fixtures are replaced by syncing real products from Tripletex and randomly assigning three specific ones (TJN10001, TJN10018, TJN10010) to the seeded employees and contract lines — the same live-Tripletex-call pattern the seed script already uses for customers and customer locations.

## Capabilities

### New Capabilities
- `products`: Tripletex-sourced, read-only master data for the TJN-prefixed product subset used to qualify employees and contract lines.

### Modified Capabilities
- `admin-portal`: removes the Skill list/detail, CRUD, and cross-reference-read-only requirements; adds a read-only Products list/detail view and a "Refresh products from Tripletex" trigger; updates the Contract list/detail and contract-line CRUD requirements' wording from skills to products.
- `employees`: `Employee` data model, list API, "can have multiple skills," and CRUD requirements change from skills to products.
- `employee-management`: employee list/detail view and CRUD requirements change from skills to products.
- `contracts`: `ContractLine` data model, "can require multiple skills," and CRUD requirements change from skills to products.
- `route-optimization`: the hard-constraints requirement's skill match becomes a product match; every requirement whose scenario text mentions "required skills" as an illustrative condition is updated to "required products" for terminology consistency.
- `assignments`: the Planning app's employee/visit cards and region/skill filters change to region/product.
- `day-planning`: the timeline block's full-detail view and the employee row label's badge both change from skills to products.
- `customer-portal`: the read-only Contract detail view's "required Skills" display changes to "required Products."
- `service-visits`: the data model and list-API requirements' "skill requirements"/"required skills" wording changes to products.
- `ad-hoc-visits`: the free-slot search requirement's skill-matching condition becomes a product-matching condition.

## Impact

- `backend/app/models.py`: `Skill` → `Product` (gains Tripletex-sourced fields: `number`, `name`, no local rename); `employee_skills`/`contract_line_skills` → `employee_products`/`contract_line_products`; `Employee.skills`/`ContractLine.required_skills` renamed accordingly.
- `backend/app/tripletex.py`: new `get_products()` (mirroring `get_customers()`/`get_delivery_addresses()`, filtered client-side to numbers starting with "TJN" — the API's `number` param turned out to filter by numeric id, not by substring) and `sync_products(db)` (mirroring `sync_customers`'s upsert/soft-delete/restore pattern).
- `backend/app/main.py`, `backend/app/schemas.py`: `/skills` CRUD endpoints removed; new `GET /products` (list) and `POST /products/sync` endpoints; every `skill_ids`/`required_skill_ids` payload field renamed to `product_ids`/`required_product_ids`.
- `backend/alembic/versions/`: a new migration drops `skills`, `employee_skills`, `contract_line_skills` and creates `products`, `employee_products`, `contract_line_products`. **This is a destructive, irreversible migration** — any existing skill assignments are lost; there is no automated skill-to-product data migration, since the two are different data sources with no defined mapping between them.
- `solver/app/domain.py`, `solver/app/constraints.py`, `backend/app/solver_client.py`: `skill_ids`/`required_skill_ids` renamed to `product_ids`/`required_product_ids`; the "Missing required skill" constraint renamed "Missing required product" with identical (subset-match) logic.
- `frontend/`: `SkillsView.tsx` deleted; new read-only `ProductsView.tsx` in the Admin Portal; `ContractsView.tsx` (Admin Portal)'s required-skills checkboxes become a multi-select product dropdown; `EmployeesView.tsx`, `ListFilterBar.tsx`/`listFilter.ts`, `DayPlanningView.tsx`, and the Customer Portal's read-only displays all rename skill→product; `types.ts`/`api.ts` renamed accordingly.
- `backend/app/seed.py`: skill fixtures replaced by a `sync_products(db)` call plus random assignment of TJN10001/TJN10018/TJN10010 to seeded employees and contract lines.
