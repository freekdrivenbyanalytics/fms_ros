## Why

The day planning page shows each employee's assignments as a timeline, but a planner can't see where those visits actually are or how an employee would drive between them in a day. A map of each employee's actual driving route makes it possible to spot inefficient or infeasible routing at a glance, on the same day a planner is already reviewing.

## What Changes

- Add a map to the day planning page, alongside the existing timeline, for the same selected day.
- For every employee with at least one assignment that day, draw their day's route on the map: home -> first visit -> ... -> last visit, in planned-start order, using TomTom's Calculate Route API to get an actual road-following path for each leg (not a straight line).
- Each employee's route is drawn in a distinct color, with a marker at each visit location; hovering/clicking a route segment or marker shows the employee name and, for a visit marker, the customer name and planned time (consistent with the existing timeline block detail).
- An employee with no assignments that day has no route drawn (nothing to route between).

## Capabilities

### Modified Capabilities
- `day-planning`: adds a route map alongside the existing timeline chart, requiring one more piece of information (a rendered route per employee) on the same page and for the same selected day.

## Impact

- `backend/app/main.py` / a new backend endpoint: given a date, return each employee's ordered visit-location sequence (home + assignment locations for that day) and the road-following route geometry between consecutive stops, computed via TomTom's Calculate Route API (`backend/app/tomtom_routing.py` already wraps TomTom for the Matrix API; this reuses the same API key/config but calls a different TomTom endpoint).
- `frontend/src/components/DayPlanningView.tsx`: add a map panel using Leaflet (already a dependency, used today in `frontend/src/shared/GeoShapeEditor.tsx`) rendering one polyline per employee per leg plus visit markers.
- New TomTom API usage: one Calculate Route call per consecutive leg per employee per day the map is viewed (not cached like the region driving-time matrix), so viewing the map repeatedly re-fetches routes.
