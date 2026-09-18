## Why

The published entity-relationship diagram ("Field Ops Schema", last updated 2026-08-24) reflects a 9-table schema from before this session's work. Since then, `backend/app/models.py` has grown substantially — Resco sync fields, the master-data CRUD fields (`archived`, `product_type`, etc.), and a full rebuild of the qualification model (`Product.employees`/`employee_products` removed; `Skill`, `ServiceOrderType`, `product_skills`, `employee_skills` added) — none of which the diagram shows. It needs regenerating from the current schema so it's a trustworthy reference again.

## What Changes

- Regenerate the entity-relationship diagram from the current `backend/app/models.py`, covering every table that exists today (roughly two dozen, up from 9), their columns with primary/foreign keys marked, and every relationship's cardinality.
- Republish it to the existing "Field Ops Schema" artifact (same URL), rather than creating a new one, so any existing link/bookmark to it keeps working.
- No application code, API, or database schema changes — this is a documentation deliverable derived from the existing model definitions, exactly like the change it supersedes.

## Capabilities

No capabilities are introduced or modified — this change produces a documentation artifact only and does not alter any system requirement or behavior. `skip_specs: true` is set in `.openspec.yaml`.

## Impact

- **Affected code**: None. Read-only reference against `backend/app/models.py`.
- **Affected systems**: Documentation only; no runtime, API, or schema impact.
- **Dependencies**: None. Reflects the schema as it exists today (the four other pending changes proposed alongside this one — navigation/forms, authentication, the customer dashboard, and parallel solving — each add their own new tables; this diagram will need a follow-up refresh once any of those are applied, not before).
