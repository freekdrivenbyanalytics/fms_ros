## Why

The route optimizer currently minimizes total straight-line (Haversine) distance between an employee's same-day visits. Straight-line distance ignores the actual road network, so it can prefer schedules that are actually slower to drive in practice. Replacing it with real driving times computed via the TomTom routing platform lets the optimizer prefer schedules that are genuinely faster to execute. TomTom is used instead of HERE because its licensing permits use in a commercial product and its free tier is more generous.

## What Changes

- Add a new `driving-times` capability: for a region, persist a single driving time (minutes) for every ordered pair of that region's location endpoints — its non-deleted customer locations and the home locations of employees scoped to it. This is a static, typical driving time, not conditioned on time of day or day of week. Driving time is directional (A→B is stored separately from B→A).
- The matrix for a region is computed on demand via a new "Compute driving times" action (mirroring the existing "Re-assign regions" action), which calls the TomTom Matrix Routing API v2 once for that region's current location set and replaces any previously stored entries for that region.
- Add a "Compute driving times" action to the Admin Portal's Regions view, alongside the existing "Re-assign regions" action.
- **BREAKING**: The route-optimization capability's soft travel constraint changes from minimizing total geographic distance (km) to minimizing total driving time (minutes), looked up from the driving-time matrix for each ordered pair of locations. A same-employee-same-day visit pair that has no matching driving-time entry (never computed, or spans a region boundary for an employee scoped to multiple regions) falls back to a Haversine-distance-based estimate for that pair only, so the optimizer never treats an uncomputed or cross-region route as free or forbidden.
- The optimizer now also scores an employee's driving time from their home location to their visits that day, using the same matrix (with the same Haversine fallback) — a cost the optimizer does not consider at all today.
- TomTom API credentials are held server-side only, following the same pattern as existing Tripletex credentials.

## Capabilities

### New Capabilities
- `driving-times`: Persists a per-region, directional driving-time matrix between the region's customer locations and scoped employees' home locations, computed on demand from the TomTom Matrix Routing API v2.

### Modified Capabilities
- `route-optimization`: The soft travel-minimization constraint changes from straight-line distance to TomTom-sourced driving time (with a Haversine fallback for uncomputed or cross-region pairs), and now also accounts for an employee's home-to-visit travel.
- `admin-portal`: Adds a "Compute driving times" action to the Regions view.

## Impact

- **Backend**: new `DrivingTime` persistence (region-scoped, directional, keyed only by ordered location pair), a new TomTom API client module (mirroring `geocoding.py`'s/`tripletex.py`'s pattern), a new `POST` endpoint to trigger a region's computation, and a new setting (`tomtom_api_key`) in `backend/app/config.py`.
- **Solver payload/domain** (`backend/app/solver_client.py`, `solver/app/schemas.py`, `solver/app/domain.py`, `solver/app/constraints.py`): visits and employees gain a location identity (not just raw lat/lon) so the solver can look up matrix entries; the travel-distance soft constraints are replaced with travel-time lookups plus Haversine fallback; a new employee-home-to-visit travel constraint is added.
- **Frontend**: `frontend/src/admin-portal/RegionsView.tsx` gains a "Compute driving times" button and result/progress feedback, next to "Re-assign regions".
- **External dependency**: introduces a billed (with a free tier), rate-limited third-party API (TomTom); this proposal does not change how existing Tripletex or Nominatim geocoding integrations work. Setup instructions for obtaining and configuring a TomTom API key are included in design.md.
