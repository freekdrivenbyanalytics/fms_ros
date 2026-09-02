## Context

See proposal.md - Why. The Contract/Contract Line backend endpoints (`create_contract`, `update_contract`, `delete_contract`, `create_contract_line`, `update_contract_line`, `delete_contract_line`, all in `backend/app/main.py`) are portal-agnostic HTTP endpoints — they don't know or care which frontend calls them. `AdminPortalApp.tsx` already fetches `contracts` and `customerLocations` via `listContracts()`/`listCustomerLocations()` (added when those views were stubbed out for future use) but doesn't render anything with them yet. `CustomerLocation` today has no lock flag and `region_id` is only ever set by `seed.py`; `tripletex.py`'s `_geocode_location` is called from exactly three sync branches (new location, restored-from-deleted, address changed) and only ever overwrites lat/lng on a successful geocode, never clearing them on failure. No point-in-polygon utility exists anywhere in this codebase yet.

## Goals / Non-Goals

**Goals:**
- Relocate Contract/Contract Line CRUD to the Admin Portal without touching the backend endpoints themselves.
- Let a planner correct a customer location's coordinates and protect that correction from being silently overwritten by the next sync.
- Let a planner derive customer locations' regions from their coordinates and each region's geo-shape on demand, decoupled from Tripletex sync entirely, so adjusting a geo-shape can be immediately followed by re-assigning without a sync round-trip.

**Non-Goals:**
- Any change to the Contract/Contract Line backend endpoints' validation or shape — only the frontend caller moves.
- Manual region override for a customer location. Region stays fully derived; a location a geofence result feels wrong for needs its geo-shape adjusted, not a per-location override.
- Handling overlapping region geo-shapes with any particular precedence rule beyond "pick the first match found" (see Risks).
- Any change to `seed.py`'s own fallback region-assignment loop — it needs one new call, not a rewrite (see D4).
- Running geofencing automatically on any schedule or trigger other than an explicit button click.

## Decisions

### D1: Contract/Contract Line CRUD moves by relocating frontend code, not by touching the backend
`frontend/src/customer-portal/ContractsView.tsx` (list, create form, detail, line form, line row with generated-visits display) is moved essentially as-is to `frontend/src/admin-portal/ContractsView.tsx`, wired into `AdminPortalApp.tsx`'s existing `Entity` union/nav pattern (already `"regions" | "skills"`, extended to include `"contracts"` and `"customer-locations"`). The Customer Portal's own `ContractsView.tsx` is rewritten as a much smaller read-only list/detail component (mirroring `CustomerLocationsView.tsx`'s existing read-only shape) that still shows a contract's lines and each line's generated visits, just without any of the CRUD forms/handlers.

### D2: `coordinates_locked` is a plain boolean on `CustomerLocation`, checked at every geocode call site
Add `coordinates_locked: Mapped[bool]` (default `False`, same pattern as every other `delete_flag`). `tripletex.py`'s three `_geocode_location` call sites (new location, restored, address-changed) each gain an `if not location.coordinates_locked:` guard around the geocode call — the location's other Tripletex-sourced fields still sync normally either way; only the geocode step is skipped. A new backend endpoint (`PATCH /customer-locations/{id}/coordinates`, body `{latitude, longitude, coordinates_locked}`) is the only way to set coordinates or the lock manually — kept separate from a general "update customer location" endpoint (which doesn't otherwise exist, since every other field is Tripletex-owned) so the API surface makes clear that coordinates+lock are the only human-editable part of a customer location.

### D3: Geofencing is a small standalone function, triggered on demand — not wired into sync at all
Add `assign_regions_by_geofence(db)` (e.g. in a new `backend/app/geofencing.py`, mirroring the `employee_schedule.py`/`visit_generation.py` precedent of small focused modules): fetch every non-deleted region with a non-null `geo_shape`, and every non-deleted customer location; for each location with resolved coordinates, run a standard ray-casting point-in-polygon test against each region's shape (treating `geo_shape`'s `[{lat, lng}, ...]` array as an ordered simple polygon) — on exactly one match, set `location.region_id` to it; otherwise (no match, or no resolved coordinates) set `location.region_id` to `None`. Per your explicit ask, this always reflects the current geofence result rather than preserving a stale prior assignment. Exposed via `POST /customer-locations/assign-regions`, called only when a user clicks "Re-assign regions" in the Admin Portal's Regions view. Deliberately **not** called from `sync_customer_locations` — per your explicit ask, region assignment shouldn't depend on triggering a Tripletex refresh, and a planner adjusting a geo-shape should be able to re-run it immediately without a sync round-trip. Alternative considered: keep it in the sync pipeline as originally designed. Rejected because it coupled two independently-useful actions (pulling fresh Tripletex data vs. recomputing regions from already-current coordinates) behind one trigger, and because re-drawing a shape shouldn't require faking or waiting for a Tripletex change to see the effect.

### D4: `seed.py` calls the geofencing function directly, mirroring what a user would click
Since geofencing is no longer wired into `sync_customer_locations`, `seed.py` must call `assign_regions_by_geofence(db)` itself (once, right after its existing `sync_customer_locations(db)` call) for seeded demo data to reflect real geo-shapes where one exists — otherwise every seeded location would fall through to `seed.py`'s own default/random region loop, since nothing else would ever run geofencing for demo data. This exactly mirrors what a planner would get from clicking the button, so it's not new behavior — just making sure the demo dataset isn't left worse off by decoupling geofencing from sync. `seed.py`'s existing `if location.region_id is not None: continue` guard already defers to whatever geofencing assigned, so no other change to that loop is needed — and since geofencing now clears `region_id` rather than leaving it alone on a non-match, that guard correctly falls through to seed's own default/random choice for those locations too, instead of skipping them over a stale leftover value.

### D5: Multiple matching regions resolve to the first found, not an error
If a location's coordinates happen to fall inside more than one region's geo-shape (overlapping shapes, a planner's drawing mistake), `assign_regions_by_geofence` picks the first match in region-id order rather than raising or leaving it unassigned. This is a pragmatic default for a condition that shouldn't normally occur; see Risks.

### D6: `GeoShapeEditor` gains a `customerLocations` prop rendered as a distinct, non-interactive marker layer
`frontend/src/shared/GeoShapeEditor.tsx`'s container height doubles (`320px` → `640px` — a plain constant change, nothing configurable). It also accepts a new optional `customerLocations: { latitude: number; longitude: number; address?: string }[]` prop; `RegionsView.tsx` passes it every customer location that has resolved coordinates (already available there via its existing `customerLocations` prop — no new data fetching needed). These render with a different `L.divIcon` (smaller, a different color, e.g. slate rather than the shape's emerald) than the shape's own point markers, and are **not** draggable and don't participate in click-to-add-point — they're purely a visual reference so a planner can see which locations a shape would or wouldn't cover before saving. Since `GeoShapeEditor` is a shared component (also usable elsewhere in principle), the prop is optional and defaults to an empty list rather than making every caller pass it.

## Risks / Trade-offs

- [Risk] Overlapping region geo-shapes produce a deterministic but possibly-surprising "first match wins" result. → Mitigation: acceptable for now since shapes are hand-drawn by a planner who can adjust them; worth a future validation step (reject/warn on overlapping shapes) if this becomes a real problem.
- [Risk] Point-in-polygon on a hand-drawn, possibly self-intersecting or very complex shape could behave unexpectedly at edges. → Mitigation: standard ray-casting handles simple (non-self-intersecting) polygons correctly, which is what the Admin Portal's map editor produces; not hardened against pathological input, consistent with how `geo_shape` was already stored without server-side well-formedness validation.
- [Trade-off] Geofencing re-checks every location with coordinates on every button click (a full scan, not an incremental update, and not scoped to a single region even when adjusting just one shape). Acceptable at this data volume (dozens of locations, a handful of regions); would need optimizing if either grew by orders of magnitude.
- [Trade-off] Locking coordinates only blocks geocoding, not the rest of a location's Tripletex-sourced fields (address, name, etc.) from updating normally. This matches your original ask (protect the coordinates specifically) rather than freezing the whole record.
- [Trade-off] Clicking "Re-assign regions" clears a location's region whenever it no longer matches any shape (rather than leaving a stale prior value in place) — so shrinking or removing a region's geo-shape can un-assign locations that used to fall inside it. This is intentional per your request: the result should always reflect the current shapes, not a mix of current and historical assignments.

## Migration Plan

1. New Alembic migration adds `customer_locations.coordinates_locked` (Boolean, `server_default=false`). Purely additive.
2. No backfill needed — every existing location defaults to unlocked, so today's geocoding behavior is unchanged until someone explicitly locks a location.
3. Rollback: `downgrade()` drops the column.
