## 1. Schema Review

- [x] 1.1 Re-read `backend/app/models.py` in full to confirm the current table list, every column, primary keys, foreign keys, and relationship cardinalities (one-to-many, many-to-many), including everything added since the last diagram: Resco sync fields, master-data CRUD fields (`archived`, `product_type`, `resco_product_id`, etc.), and the skills/service-order-types rebuild (`Skill`, `ServiceOrderType`, `product_skills`, `employee_skills`; `Product.employees`/`employee_products` no longer exist)
- [x] 1.2 Cross-check the table list against `backend/alembic/versions/` (latest revision) to confirm nothing in the live database has diverged from what `models.py` declares

## 2. Diagram Update

- [x] 2.1 Rebuild the entity-relationship diagram covering every current table and association table
- [x] 2.2 Show each table's columns with primary keys marked, and connect tables with relationship lines labeled with cardinality (1—N, N—N)

## 3. Publish

- [x] 3.1 Republish the diagram to the existing "Field Ops Schema" Artifact (https://claude.ai/artifact/WaGfmVC6UM6N89SNhNJeWd), preserving its URL rather than creating a new one
- [x] 3.2 Share the resulting link with the user for review
