## Context

`DayPlanningView.tsx` already receives the full `assignments` list as a prop and filters it to the selected day client-side (see `dayAssignments`/`assignmentsByEmployee`). Employee home coordinates (`latitude`/`longitude`) and each assignment's customer-location coordinates (via `service_visit.contract_line.customer_location`) are already present in the data the frontend has, or one join away in the backend. What's missing is road-following route *geometry* between stops: `backend/app/tomtom_routing.py` only calls TomTom's Matrix Routing API, which returns travel-time/distance summaries, not a path. Drawing an actual route requires TomTom's separate Calculate Route API. See proposal.md for why this is being added and the decision to call TomTom live rather than reuse straight lines.

## Goals / Non-Goals

**Goals:**
- Get road-following polyline geometry for each employee's day-route (home -> visits in planned order) from TomTom, server-side (the TomTom API key is backend-only, matching how `tomtom_routing.py` already keeps it out of the frontend).
- Keep the frontend's job to rendering: it already knows how to filter assignments to a day and hold a Leaflet map (`GeoShapeEditor.tsx`); the new map panel reuses that pattern rather than introducing a second mapping approach.

**Non-Goals:**
- Turn-by-turn navigation, ETAs, or live traffic - this is a review visualization, not a driving aid.
- Caching or persisting route geometry (unlike the region driving-time matrix, which is a precomputed, persisted table) - the proposal explicitly accepts recomputing on each view, since route geometry is only needed while the map is open, not scored by the solver.

## Decisions

**New backend endpoint returns fully-resolved routes, not raw coordinates.** `GET /day-planning/routes?date=YYYY-MM-DD` computes, per employee with >=1 assignment that day: the ordered stop list (home, then each assignment's customer location ordered by `planned_start`) and the route geometry connecting them, then returns both together with enough visit/employee detail (names, planned times) for the frontend to render markers and popups without a second round-trip. Alternative considered: have the frontend send its already-fetched assignment list and just ask the backend for geometry - rejected because the backend already owns this exact "what's assigned on what day" query shape (`build_optimize_payload`'s date-filtering logic is a close precedent), and keeping route-ordering server-side avoids the frontend and backend disagreeing about stop order.

**One TomTom Calculate Route call per employee per day, using multi-waypoint routing, not one call per leg.** TomTom's Calculate Route API accepts a colon-separated chain of coordinates in a single request and returns the full route (with a `legs` breakdown mirroring the waypoints) in one response. Calling it once per employee with all of that day's stops chained, instead of once per consecutive pair, cuts the API call count roughly N-fold for an employee with N stops and avoids re-deriving how per-leg geometry should be stitched into one polyline for rendering.

**A new `tomtom_routing.py` function (e.g. `compute_employee_day_route`), not a new module.** It's the same TomTom credential, same `httpx` client pattern, and the same "kind"/coordinate concepts (`LocationEndpoint`) already defined there; a separate module would just re-import all of that.

**No result caching for v1.** Route geometry depends on which day is selected and today's assignment state, and the proposal already accepts re-fetching per view. Mitigation for repeated TomTom calls is addressed below rather than built now.

## Risks / Trade-offs

**Extra TomTom API usage (and cost) every time the map is viewed**, unlike the region driving-time matrix which is computed once and persisted. → Mitigation: scoped to only employees with assignments that day (not the whole roster), and a single multi-waypoint call per employee rather than per leg; if usage becomes a concern later, the response shape (route keyed by employee + date) makes adding a short-lived cache straightforward without a spec change.

**TomTom's Calculate Route API can fail or return no route for a leg** (e.g. an unreachable coordinate), the same class of failure `compute_region_driving_times` already handles for the Matrix API by skipping that pair. → Mitigation: an employee whose route call fails or returns no route is omitted from the map response (with the rest of the day's employees still rendered), rather than failing the whole request.

**Frontend map panel duplicates some Leaflet setup already in `GeoShapeEditor.tsx`** (tile layer, map lifecycle) since that component is a single-shape editor, not a multi-route viewer, and isn't a natural fit to extend in place. → Accepted: a second, smaller Leaflet component for rendering (no editing, no click-to-add-point) is simpler than generalizing the editor to also be a read-only multi-route viewer.
