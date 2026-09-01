## Why

Regions today are a fixed, name-only lookup table seeded once and browsed read-only from the Customer Portal — there's no way to create, rename, or retire one, and no way to capture a region's actual geographic extent. Planning needs regions to eventually be assignable automatically from a location's coordinates, which first requires regions to carry a real geo-shape. This change introduces a new "Admin Portal" area — the first home for internal, planner-facing masterdata management that doesn't belong in the customer-facing portal — and moves region management there with full CRUD and a map for drawing/editing each region's geo-shape.

## What Changes

- Add a new, separate top-level frontend area ("Admin Portal") — its own entry point, sharing no navigation with Planning, the Customer Portal, or Employee Management — intended over time to hold other internal masterdata management currently living in the Customer Portal. This change moves only Regions into it.
- **BREAKING**: Remove the Regions list/detail view from the Customer Portal. Regions are no longer visible or manageable there.
- Add full CRUD (create, update, soft-delete) for regions from the Admin Portal: name and an optional geo-shape. Soft-delete follows the existing `delete_flag` pattern used elsewhere.
- Add a `geo_shape` field to Region: an optional polygon (an ordered list of latitude/longitude coordinate pairs) describing the region's geographic extent. Existing regions keep working with no geo-shape until one is added.
- Add a map-based editor in the Admin Portal for drawing a new geo-shape or adjusting an existing one, by placing/moving coordinate points.
- The Admin Portal's Region detail view shows the same read-only cross-references the Customer Portal's did: the employees scoped to that region and the customer locations located in it.

## Out of Scope

- Automatically assigning a customer location's region from its coordinates and a region's geo-shape (geofencing). This change only captures the geo-shape; using it to derive an assignment is a later iteration.
- Any change to how customer locations get their region today: that remains exactly as it is now (assigned only via seed data), per your explicit answer that this stays read-only until the future geofencing-based change.
- Any change to how employees get their regions today: that remains exactly as it is now, editable from the Employee's own form in Employee Management (unchanged, not duplicated into the Admin Portal).

## Capabilities

### New Capabilities
- `admin-portal`: the standalone frontend area for internal masterdata management — its separateness from Planning/Customer Portal/Employee Management, and (for this iteration) region list/detail views with full CRUD and geo-shape editing.

### Modified Capabilities
- `regions`: data model gains an optional geo-shape and a soft-delete flag; adds create/update/soft-delete requirements and a "deleted regions are hidden by default" requirement.
- `customer-portal`: remove Regions from the portal's entity list, list views, detail views, and every requirement/scenario that names it.

## Impact

- Backend: `Region` gains `geo_shape` (nullable) and `delete_flag`; new migration; new schemas/endpoints for region CRUD; `GET /regions` excludes soft-deleted regions by default.
- Frontend: new top-level entry point + app (mirroring `customer-portal.html`/`employee-management.html`) for the Admin Portal, with its own list/detail/CRUD views for regions and a map component for geo-shape editing (new mapping dependency); `RegionsView.tsx` and its region-specific logic removed from the Customer Portal.
- No change to the route optimizer, to customer location data, or to employee-region assignment.
