## 1. Backend data model & migration

- [x] 1.1 In `backend/app/models.py`: add `geo_shape` (JSONB, nullable) and `delete_flag` (Boolean, default False, server_default "false") to `Region`.
- [x] 1.2 New Alembic migration `0009_region_geo_shape.py`: add `regions.geo_shape` (JSONB, nullable) and `regions.delete_flag` (Boolean, `server_default=false`). Purely additive — no truncation, no backfill. Write a `downgrade()` that drops both columns.
- [x] 1.3 Run `alembic upgrade head`, then `alembic downgrade 0008`, then `alembic upgrade head` again to confirm both directions work cleanly against the running Postgres container.

## 2. Backend API

- [x] 2.1 Add `RegionOut` (id, name, geo_shape), `RegionCreate` (name, geo_shape optional), `RegionUpdate` (name, geo_shape optional) schemas in `backend/app/schemas.py`. Validate in the schema or endpoint that a non-null `geo_shape` has at least 3 coordinate pairs.
- [x] 2.2 Add `POST /regions`, `PATCH /regions/{id}`, `DELETE /regions/{id}` (soft) in `backend/app/main.py`; update `GET /regions` to exclude `delete_flag=True` by default.
- [x] 2.3 Verify via API: creating a region with just a name works (geo_shape null); updating a region to add a geo_shape of 3+ points works; a geo_shape with fewer than 3 points is rejected (422); soft-deleting a region excludes it from `GET /regions` while leaving referencing employees/customer locations unaffected.

## 3. Frontend: shared types and API client

- [x] 3.1 Update `frontend/src/types.ts`: extend `Region` with `geo_shape: { lat: number; lng: number }[] | null`; add `RegionCreateInput`/`RegionUpdateInput`.
- [x] 3.2 Add `createRegion`, `updateRegion`, `deleteRegion` to `frontend/src/api.ts`, following the existing create/update/delete patterns (manual 204 handling for delete).
- [x] 3.3 Add the `leaflet` and `@types/leaflet` dependencies to `frontend/package.json`.

## 4. Frontend: map-based geo-shape editor

- [x] 4.1 Create `frontend/src/shared/GeoShapeEditor.tsx`: a Leaflet map (OpenStreetMap tiles) that renders an existing `geo_shape` as a polygon if present, lets a user click to add points, drag a point marker to move it, remove the last point, and exposes the current point list to the parent via an `onChange` callback. Handle the empty-shape case (no polygon shown, ready to draw).
- [x] 4.2 Manually verify in the browser: drawing a new shape by clicking 3+ points renders a polygon; dragging a point updates the polygon live; removing a point updates it; the component correctly renders a region that already has a geo_shape.

## 5. Frontend: new Admin Portal area

- [x] 5.1 Add `admin-portal.html` at the project root (mirroring `customer-portal.html`/`employee-management.html`) and register it in `vite.config.ts`'s `rollupOptions.input`.
- [x] 5.2 Create `frontend/src/admin-portal/main.tsx` and `AdminPortalApp.tsx` providing its own top-level layout with no Planning/Customer Portal/Employee Management navigation, fetching regions, employees, and customer locations.
- [x] 5.3 Create `frontend/src/admin-portal/RegionsView.tsx`: list view (using the shared `ListTable`) and detail view (using the shared `DetailField`) showing a region's name, geo-shape editor (`GeoShapeEditor`), the employees scoped to it (read-only, client-side filtered), and the customer locations in it (read-only, client-side filtered).
- [x] 5.4 Implement region CRUD forms in `RegionsView.tsx`: create (name only), update (name + geo-shape via `GeoShapeEditor`, with a Save action), and soft-delete.
- [x] 5.5 Add an "Admin Portal" nav link next to "Customer Portal" and "Employee Management" in `frontend/src/App.tsx`'s top nav.

## 6. Frontend: remove Regions from the Customer Portal

- [x] 6.1 Delete `frontend/src/customer-portal/RegionsView.tsx` and remove the Regions list/detail route and nav entry from `CustomerPortalApp.tsx`.
- [x] 6.2 Remove any now-unused `regions` fetching/state from `CustomerPortalApp.tsx` (keep fetching regions only if still needed elsewhere in the portal, e.g. for Customer Location detail's region name display — check before removing).

## 7. End-to-end verification

- [x] 7.1 Run `tsc -b` and confirm the frontend type-checks cleanly.
- [x] 7.2 Launch frontend + backend and manually confirm in the browser: the Admin Portal is reachable as its own top-level page with no Planning/Customer Portal/Employee Management nav; region create/update/soft-delete work end-to-end; drawing and adjusting a geo-shape on the map persists correctly (reload the page and confirm it's still there); a region's detail view shows the correct read-only employee/customer-location cross-references; the Customer Portal no longer shows Regions anywhere (nav, lists), while Customer Location detail still shows each location's region name.
- [x] 7.3 Confirm `openspec validate --strict` passes for the change before archiving.
