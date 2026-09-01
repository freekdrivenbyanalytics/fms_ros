## Context

See proposal.md - Why. `Region` (backend/app/models.py) is currently `{id, name}` only, referenced by `CustomerLocation.region_id` (nullable FK) and the `employee_regions` many-to-many table. It has no `delete_flag` yet — it's the one remaining master-data entity in this codebase without soft-delete. The Customer Portal (`frontend/src/customer-portal/`) and Employee Management (`frontend/src/employee-management/`) are the two existing precedents for a new standalone Vite entry (own `*.html`, own `main.tsx`/`*App.tsx`, registered in `vite.config.ts`'s `rollupOptions.input`), and for the "read soft-deleted-filtered list, full CRUD, detail view with read-only cross-references" shape now being extended to regions.

## Goals / Non-Goals

**Goals:**
- Full region CRUD (name, geo-shape, soft-delete) from a new Admin Portal area.
- Capture a region's geo-shape as a simple polygon, editable via a map, with no computation performed on it yet.
- Preserve the exact read-only cross-reference views (employees scoped to a region, customer locations in it) that the Customer Portal's Region detail already showed, just relocated.

**Non-Goals:**
- Geofencing / auto-assigning a customer location's or employee's region from coordinates (explicit later iteration per proposal.md).
- Any editable region-assignment control for customer locations or employees inside the Admin Portal (per your answer: customer location region stays seed-data-only; employee region assignment stays on Employee Management, not duplicated here).
- Multi-polygon or hole-having regions, or any shape besides a single simple polygon.
- Any other Customer Portal entity moving to the Admin Portal — this change moves only Regions.

## Decisions

### D1: `geo_shape` stored as a plain JSON array of coordinate pairs, not a geometry column
Store `Region.geo_shape` as `JSONB` (nullable), holding `[{"lat": ..., "lng": ...}, ...]` in point order, mirroring the existing `dict | None` / `JSONB` pattern already used for Tripletex's nested `Customer` fields. Alternative considered: a PostGIS `geometry(Polygon)` column. Rejected — PostGIS isn't installed anywhere in this stack (plain `postgres:16-alpine` in `docker-compose.yml`), and since no geofencing/spatial query runs against it in this change (explicitly deferred), a geometry column would add a new infrastructure dependency for zero present benefit. Revisit this decision if/when the deferred auto-assignment iteration needs real spatial queries (`ST_Contains`, etc.) rather than just storage.

### D2: A hand-rolled polygon editor on top of Leaflet, not a drawing plugin
Add `leaflet` (and `@types/leaflet`) as the only new frontend dependency; render a `<MapContainer>`-equivalent imperatively (this codebase uses plain Leaflet-style imperative DOM APIs elsewhere have no React wrapper libraries at all — `react-leaflet` would be the first component-library dependency in a codebase that otherwise hand-rolls its UI). Tiles come from OpenStreetMap, consistent with the geocoding precedent (`geopy` + Nominatim, both OSM-backed) already established in `add-tripletex-location-sync`. The polygon editor itself is a small hand-rolled interaction (click to add a point, drag an existing point marker to move it, a button/right-click to remove the last point, a "Save" action to persist) rather than pulling in `leaflet-draw` — the interaction is simple enough (one polygon, no holes, no multi-shape) that a plugin adds more surface area (its own CSS, icon assets, event model) than it saves.

### D3: Region soft-delete follows existing precedent exactly
Add `delete_flag` to `Region` the same way as every other entity (`Customer`, `CustomerLocation`, `Contract`, `ContractLine`, `Employee`, ...): `Boolean, nullable=False, default=False, server_default="false"`. No usage guard on delete (soft-deleting a region in use by employees/customer locations is allowed, exactly like soft-deleting a `Contract` doesn't check for existing service visits) — consistent with how every other soft-delete in this codebase behaves.

### D4: Admin Portal reuses the shared `ListTable`/`DetailField` components
`frontend/src/shared/ListTable.tsx` and `DetailField.tsx` (already extracted from the Customer Portal during `add-employee-scheduling`) are reused as-is for the region list/detail views — no new shared components needed beyond the map.

### D5: Region detail's cross-reference lists are computed client-side from already-fetched data, not new endpoints
The Customer Portal's Region detail today computes "employees scoped to this region" and "customer locations in this region" by filtering the already-fetched `employees`/`customerLocations` arrays client-side (see `RegionsView.tsx` before this change). The Admin Portal does the same: it fetches `listEmployees()` and `listCustomerLocations()` alongside `listRegions()` and filters client-side. No new backend endpoint is needed for these cross-references.

## Risks / Trade-offs

- [Risk] A hand-rolled Leaflet polygon editor is more code than a drawing plugin would need, and has to be built (not just configured). → Mitigation: the interaction is intentionally minimal (single polygon, point add/move/remove only — no multi-shape, no holes, no snapping), keeping the hand-rolled surface small.
- [Risk] Storing `geo_shape` as plain JSON means no database-level validation that it's a well-formed, non-self-intersecting polygon. → Mitigation: acceptable for this iteration since nothing consumes the shape computationally yet; write-time validation (≥3 points) happens at the API layer, matching how other structural rules in this codebase are enforced outside the DB.
- [Trade-off] Not supporting map-based visual assignment of customer locations to a region in this iteration (per your answer) means the map is view/edit-shape-only for now — this is intentional, not an oversight, and matches the explicitly deferred auto-assignment iteration.

## Migration Plan

1. New Alembic migration adds `regions.geo_shape` (JSONB, nullable) and `regions.delete_flag` (Boolean, `server_default=false`). Purely additive — no truncation or backfill needed, unlike prior migrations that restructured Tripletex-sourced tables.
2. `seed.py`'s existing regions stay as-is (no geo-shape); nothing to change there since a null geo-shape is a fully supported state per regions spec's "An existing region without a geo-shape remains usable."
3. Rollback: `downgrade()` drops both new columns.
