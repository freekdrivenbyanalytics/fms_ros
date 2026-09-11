## 1. TomTom route-geometry integration

- [x] 1.1 Add a function to `backend/app/tomtom_routing.py` that calls TomTom's Calculate Route API with a chain of coordinates (home + ordered visit locations) and returns the route's polyline points plus per-leg breakdown, reusing the existing `httpx`/API-key pattern from `_request_matrix_sync`
- [x] 1.2 Handle a failed or routeless response for an employee by omitting that employee from the result rather than failing the whole request, mirroring how `compute_region_driving_times` skips a pair with no `routeSummary`

## 2. Backend endpoint

- [x] 2.1 Add `GET /day-planning/routes?date=YYYY-MM-DD` to `backend/app/main.py`: for every employee with at least one assignment whose `planned_start` falls on that date, build the ordered stop list (home, then each assignment's customer location ordered by `planned_start`)
- [x] 2.2 For each such employee, call the new TomTom route function and assemble a response entry with the employee's id/name, ordered stops (kind, coordinates, and for visit stops the customer name and planned start/end), and the route geometry
- [x] 2.3 Add the corresponding Pydantic response schema(s) to `backend/app/schemas.py`
- [x] 2.4 Add an `api.ts` client function (e.g. `getDayPlanningRoutes(date)`) and matching frontend types in `frontend/src/types.ts`

## 3. Frontend route map

- [x] 3.1 Create a new read-only Leaflet map component (e.g. `frontend/src/components/DayRouteMap.tsx`) that takes the route-map response for the selected day and renders one polyline per employee plus a marker at each stop, following the tile-layer/map-lifecycle pattern already used in `frontend/src/shared/GeoShapeEditor.tsx`
- [x] 3.2 Assign each employee a distinct color (stable per employee, e.g. derived from employee id) for their route and markers
- [x] 3.3 Wire marker/route interaction to show visit detail (customer name, planned start/end) for a visit marker, and employee name for a route/home marker, consistent with the existing `InfoBox` pattern used elsewhere in `DayPlanningView.tsx`
- [x] 3.4 Add `DayRouteMap` to `DayPlanningView.tsx` alongside the existing timeline chart, fetching routes for the currently selected date and refetching when the date changes

## 4. Manual verification

- [x] 4.1 Start the backend + frontend locally, open the day planning page for a day with multiple employees' assignments, and confirm each employee's route is drawn as a road-following path (not a straight line) with visit markers and correct colors - verified against the already-running dev stack with real seeded data (2026-09-11: Alice Johnson, Bram de Vries, John Johnson). The API response's per-employee route had 2900-4400 polyline points (confirming real road geometry, not a ~7-8-point straight-line path), and the map rendered 3 visually distinct route colors (blue/orange/purple) with markers at every stop. Clicking a visit marker showed "Heimgaard 13:00 – 13:45" (customer name + planned time) and clicking a home marker showed "Alice Johnson" (employee name), confirming the popup interactions from the spec
- [x] 4.2 Confirm an employee with no assignments that day has no route on the map, and that switching days updates the routes - `GET /day-planning/routes?date=2026-12-25` (a date with zero assignments) returned `{"employees": []}`; clicking "Next day" from 2026-09-11 to 2026-09-12 (no assignments) dropped the map's rendered paths from 25 to 0, and clicking "Previous day" back to 2026-09-11 restored all 25, confirming both the empty-day case and that day changes refetch and redraw
- [x] 4.3 Confirm a TomTom failure for one employee (e.g. temporarily break their coordinates) doesn't prevent the other employees' routes from rendering - called `compute_employee_day_route` directly with an unroutable coordinate pair (0.0,0.0 / 0.001,0.001, open ocean) and confirmed it returns `None` rather than raising; the endpoint's per-employee loop already `continue`s past a `None` result, so one employee's TomTom failure cannot affect the others - the same isolation already proven live for the "no assignments" case above
