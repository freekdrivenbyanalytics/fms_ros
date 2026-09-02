## 1. Backend: data model & migration

- [x] 1.1 In `backend/app/models.py`: add `coordinates_locked` (Boolean, default False, server_default "false") to `CustomerLocation`.
- [x] 1.2 New Alembic migration `0011_customer_location_coordinates_lock.py`: add `customer_locations.coordinates_locked` (Boolean, `server_default=false`). Purely additive. Write a `downgrade()` that drops the column.
- [x] 1.3 Run `alembic upgrade head`, then `alembic downgrade 0010`, then `alembic upgrade head` again to confirm both directions work cleanly.
- [x] 1.4 Add `coordinates_locked: bool` to `CustomerLocationOut` in `backend/app/schemas.py`.

## 2. Backend: skip geocoding for locked locations

- [x] 2.1 In `backend/app/tripletex.py`, guard each of the three `_geocode_location(location)` call sites in `sync_customer_locations` (new location, restored-from-deleted, address-changed) with `if not location.coordinates_locked:`.
- [x] 2.2 Verify via a direct script: a locked location's address change during sync does not update its coordinates; an unlocked location's still does (existing behavior unchanged).

## 3. Backend: coordinate override endpoint

- [x] 3.1 Add `CustomerLocationCoordinatesUpdate` schema (`latitude: float`, `longitude: float`, `coordinates_locked: bool`) in `backend/app/schemas.py`.
- [x] 3.2 Add `PATCH /customer-locations/{id}/coordinates` in `backend/app/main.py`: sets `latitude`, `longitude`, and `coordinates_locked` on the location; 404 if not found.
- [x] 3.3 Verify via API: setting coordinates with `coordinates_locked: true` persists both; a subsequent sync (simulated) does not change them; setting `coordinates_locked: false` on a previously-locked location allows a later sync to update coordinates again.

## 4. Backend: geofencing

- [x] 4.1 Create `backend/app/geofencing.py` with a point-in-polygon function (standard ray-casting) over a `geo_shape`-shaped list of `{lat, lng}` points, and `assign_regions_by_geofence(db: Session) -> None`: for every non-deleted customer location, if it has resolved latitude/longitude, test it against every non-deleted region with a non-null `geo_shape` and set its `region_id` to the match (first found if more than one); otherwise (no match, or no resolved coordinates) set its `region_id` to `None`.
- [x] 4.2 Add `POST /customer-locations/assign-regions` in `backend/app/main.py` that calls `assign_regions_by_geofence(db)` and returns the updated customer locations (or a simple count/summary). Do **not** call it from `sync_customer_locations` — region re-assignment must not run automatically as part of any Tripletex sync.
- [x] 4.3 Unit-verify the point-in-polygon function directly: a point clearly inside a simple polygon, a point clearly outside, a point on/near an edge (documented behavior either way is fine, just verify it doesn't crash or infinite-loop), and a region with a null `geo_shape` never matches anything.
- [x] 4.4 Verify via API: create or update a region with a geo_shape covering a known customer location's coordinates, call `POST /customer-locations/assign-regions`, and confirm that location's `region_id` updates; give another location a `region_id` first (e.g. via seed), then confirm that after the call, if its coordinates match no shape, its `region_id` is cleared to `None` rather than left as-is; confirm a location with no coordinates also ends up with `region_id` `None`; confirm triggering a Tripletex sync does *not* change any location's region; confirm calling the endpoint again after adjusting a geo-shape picks up the new shape (including clearing locations no longer covered).
- [x] 4.5 Add a call to `assign_regions_by_geofence(db)` in `backend/app/seed.py`, right after its existing `sync_customer_locations(db)` call and before its own per-location default/random region loop, so seeded demo data reflects real geo-shapes where one exists (mirroring what a planner clicking "Re-assign regions" would produce). The existing `if location.region_id is not None: continue` guard in that loop already defers correctly to whatever geofencing assigned — no other change needed there.

## 5. Frontend: move Contract/Contract Line CRUD to the Admin Portal

- [x] 5.1 Add `frontend/src/admin-portal/ContractsView.tsx`: move the full CRUD implementation from `frontend/src/customer-portal/ContractsView.tsx` (list, create form, `ContractDetail`, `ContractLineRow` with generated-visits display, `ContractLineForm`), adjusted to this app's props (`contracts`, `customers`, `customerLocations`, `serviceVisits`, `skills`, `onChanged`).
- [x] 5.2 Wire the new view into `frontend/src/admin-portal/AdminPortalApp.tsx`: extend its `Entity` union with `"contracts"`, add the nav entry, and pass through the `contracts`/`customerLocations` state it already fetches, plus fetch `serviceVisits` and `skills` (not yet fetched there) alongside the existing `regions`/`employees` fetches.
- [x] 5.3 Rewrite `frontend/src/customer-portal/ContractsView.tsx` as a read-only list/detail view (mirroring `CustomerLocationsView.tsx`'s existing read-only shape): list of contracts, detail showing a contract's own fields, its customer, and its lines (each showing customer location, dates, interval, duration, required skills, and generated visits) — no create/edit/delete controls anywhere.
- [x] 5.4 Remove the now-unused contract-mutation API calls (`createContract`, `updateContract`, `deleteContract`, `createContractLine`, `updateContractLine`, `deleteContractLine`) from `frontend/src/customer-portal/CustomerPortalApp.tsx`'s imports/usage if no longer referenced there; keep them in `frontend/src/api.ts` since the Admin Portal now uses them.

## 6. Frontend: Admin Portal Customer Locations view

- [x] 6.1 Add `createCustomerLocationCoordinates` (or similarly named) to `frontend/src/api.ts`, calling `PATCH /customer-locations/{id}/coordinates`; add `coordinates_locked: boolean` to the `CustomerLocation` type in `frontend/src/types.ts`.
- [x] 6.2 Add `frontend/src/admin-portal/CustomerLocationsView.tsx`: list view (address, customer, region, locked indicator) and detail view showing the location's own fields, customer, region (read-only, no control to change it), and a coordinate-override form (latitude, longitude, "don't overwrite on refresh" checkbox bound to `coordinates_locked`) with Save.
- [x] 6.3 Wire it into `AdminPortalApp.tsx`: extend `Entity` with `"customer-locations"` and add the nav entry.
- [x] 6.4 Add a `assignRegionsByGeofence` (or similarly named) call to `frontend/src/api.ts` for `POST /customer-locations/assign-regions`; add a "Re-assign regions" button to `frontend/src/admin-portal/RegionsView.tsx`'s list view that calls it and refreshes (`onChanged`) on success, showing a brief result/error message.

## 7. Frontend: bigger map with customer locations shown

- [x] 7.1 In `frontend/src/shared/GeoShapeEditor.tsx`, double the map container's height (`320px` → `640px`).
- [x] 7.2 Add an optional `customerLocations?: { latitude: number; longitude: number; address?: string }[]` prop to `GeoShapeEditor`; render each as a non-draggable marker (a distinct `L.divIcon` — different color/size from the shape's own point markers) that does not participate in click-to-add-point or dragging.
- [x] 7.3 In `frontend/src/admin-portal/RegionsView.tsx`, pass every customer location with resolved coordinates (from its existing `customerLocations` prop) into `GeoShapeEditor`'s new prop.
- [x] 7.4 Manually verify in the browser: the map is noticeably taller; customer location markers appear on it, visually distinct from the shape's own draggable point markers; clicking on or near a customer location marker still adds a shape point at that spot rather than being absorbed by the marker.

## 8. End-to-end verification

- [x] 8.1 Run `tsc -b` and confirm the frontend type-checks cleanly.
- [x] 8.2 Launch frontend + backend and manually confirm in the browser: Contract/Contract Line CRUD works fully from the Admin Portal (including the generated-visits display); the Customer Portal's Contracts view shows the same data read-only with no create/edit/delete controls anywhere in the portal; the Admin Portal's Customer Locations view lets you set coordinates and lock them, and triggering a Tripletex refresh does not change locked coordinates or any location's region; drawing a region's geo-shape over a known location's coordinates and clicking "Re-assign regions" assigns that location to the region.
- [x] 8.3 Confirm `openspec validate --strict` passes for the change before archiving.
