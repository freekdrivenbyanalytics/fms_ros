## Why

The backend database schema (`backend/app/models.py`) has grown to nine tables with several many-to-many join tables, and there is no visual reference for how they relate. New contributors and the human maintainer currently have to read SQLAlchemy model code to understand foreign keys and relationships. A published entity-relationship diagram makes the schema easy to review and share.

## What Changes

- Generate an entity-relationship diagram (ERD) covering all current database tables: `regions`, `skills`, `customers`, `customer_locations`, `contracts`, `employees`, `service_visits`, `assignments`, and the join tables `employee_regions`, `employee_skills`, `contract_skills`.
- Publish the ERD as a viewable image/artifact showing each table's columns, primary keys, foreign keys, and the relationships (one-to-many, many-to-many) between tables.
- No application code, API, or database schema changes — this is a documentation deliverable derived from the existing `backend/app/models.py` definitions.

## Capabilities

No capabilities are introduced or modified — this change produces a documentation artifact only and does not alter any system requirement or behavior. `skip_specs: true` is set in `.openspec.yaml`.

## Impact

- **Affected code**: None. Read-only reference against `backend/app/models.py`.
- **Affected systems**: Documentation only; no runtime, API, or schema impact.
- **Dependencies**: None.
