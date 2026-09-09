## 1. Backend: data model & migration

- [x] 1.1 In `backend/app/models.py`: add a `DrivingTime` model for table `driving_times` with `id`, `region_id` (FK `regions.id`, `ondelete="CASCADE"`), `origin_kind` (Enum: `customer_location`, `employee`), `origin_id`, `destination_kind` (same enum), `destination_id`, `duration_minutes`, and a unique constraint over `(region_id, origin_kind, origin_id, destination_kind, destination_id)`.
- [x] 1.2 New Alembic migration `0012_driving_times.py`: create the `driving_times` table and its enum type, matching 1.1. Write a `downgrade()` that drops the table and enum type.
- [x] 1.3 Run `alembic upgrade head`, then `alembic downgrade 0011`, then `alembic upgrade head` again to confirm both directions work cleanly.
- [x] 1.4 Add `tomtom_api_key: str = ""` to `backend/app/config.py`'s `Settings`. Add a `TOMTOM_API_KEY=` placeholder line to `backend/.env.example`.
- [x] 1.5 Create a free TomTom developer account and API key at `https://developer.tomtom.com`, and add it to `backend/.env` as `TOMTOM_API_KEY=<your-key>` (create `backend/.env` from `backend/.env.example` first if it doesn't exist yet), per design.md's "Obtaining and configuring a TomTom API key".

## 2. Backend: TomTom Matrix Routing integration

- [x] 2.1 Create `backend/app/tomtom_routing.py` with a function to build a region's location set: every non-deleted `CustomerLocation` with `region_id` equal to the region, plus the home location (latitude/longitude) of every non-deleted `Employee` scoped to the region (via `employee_regions`), each tagged with `origin_kind`/`origin_id` (`customer_location`/location.id or `employee`/employee.id).
- [x] 2.2 In the same module, add a function that calls the TomTom Matrix Routing API v2 with the region's full location set as both origins and destinations, with no departure time specified (static, non-traffic-adjusted typical travel time), returning an origin→destination duration-in-minutes mapping. Skip (log and continue) any pair TomTom cannot return a route for, per the driving-times spec's failure-tolerance requirement. Use the synchronous matrix endpoint when the location count is within TomTom's synchronous limit for the configured plan, and the asynchronous submit-then-poll job endpoint otherwise (confirm the exact threshold during implementation, per design.md's Risks).
- [x] 2.3 Add `compute_region_driving_times(db: Session, region: Region) -> dict` that: builds the location set (2.1), calls the matrix function (2.2) once, and — in a single transaction — deletes the region's existing `DrivingTime` rows and inserts the newly computed ones. Return a summary dict (e.g. `{"computed": N, "skipped": M}`).
- [x] 2.4 Verify directly against the live TomTom API (disposable test region with 2–3 real geocoded customer locations): confirm entries are persisted for every ordered pair with plausible minute values, confirm re-running replaces rather than duplicates entries, and confirm an intentionally unroutable location (e.g. one with placeholder ocean coordinates) is skipped without aborting the rest. Clean up test data afterward.

## 3. Backend: compute-driving-times endpoint

- [x] 3.1 Add `POST /regions/{region_id}/driving-times` in `backend/app/main.py`: 404 if the region doesn't exist, otherwise calls `compute_region_driving_times` and returns its summary.
- [x] 3.2 Verify via `curl` against a running backend: triggering the endpoint for a region returns a summary, and querying the `driving_times` table shows the expected rows for that region.

## 4. Backend: solver payload changes

- [x] 4.1 In `backend/app/solver_client.py`'s `_visit_payload`, add `location_id: location.id` (the visit's `customer_location_id`). Also added `location_id` to `_existing_assignment_payload` (not in the original task list, but required for task 5.4's `VisitAssignment`-to-`ExistingAssignmentFact` driving-time join to be possible at all).
- [x] 4.2 In `build_optimize_payload`, after computing `ready_visits`, gather the set of region ids actually in play (from `ready_visits`' locations and from `employees`' regions) and query `DrivingTime` rows scoped to those regions; add them to the payload as a `driving_times` list of `{origin_kind, origin_id, destination_kind, destination_id, duration_minutes}` dicts.
- [x] 4.3 Verify via a direct call to `build_optimize_payload` against the live dev DB (disposable script): confirm the `driving_times` list only includes rows for regions touched by the current candidate visits/employees, not the whole table.

## 5. Solver: domain and constraint changes

- [x] 5.1 In `solver/app/schemas.py`, add `location_id: int` to `VisitIn`, and a `DrivingTimeIn` schema (`origin_kind`, `origin_id`, `destination_kind`, `destination_id`, `duration_minutes`); add `driving_times: list[DrivingTimeIn] = []` to `OptimizeRequest`. Also added `location_id: int` to `ExistingAssignmentIn` (see 4.1's note).
- [x] 5.2 In `solver/app/domain.py`, add `location_id: int` to `VisitAssignment`; add a frozen `DrivingTimeFact` dataclass matching `DrivingTimeIn`; add `driving_times: Annotated[list[DrivingTimeFact], ProblemFactCollectionProperty]` to `Schedule`. Also added `location_id: int` to `ExistingAssignmentFact`.
- [x] 5.3 In `solver/app/solve.py`'s `_build_schedule`, pass `location_id` through for each `VisitAssignment`, and build the `driving_times` list of `DrivingTimeFact` for the `Schedule`. Also passed `location_id` through for each `ExistingAssignmentFact`.
- [x] 5.4 In `solver/app/constraints.py`, replace `_visit_distance_km`/`_visit_existing_distance_km` and the two "Travel distance" constraints with driving-time-based equivalents per design.md's D1–D5: join `VisitAssignment` pairs (and `VisitAssignment`-to-`ExistingAssignmentFact` pairs) against `DrivingTimeFact` on `(origin_kind="customer_location", origin_id=<earlier visit's location_id>, destination_kind="customer_location", destination_id=<later visit's location_id>)`, penalizing the matched `duration_minutes`; add an `if_not_exists` counterpart that penalizes a Haversine-derived minute estimate (D5) when no matching fact exists.
- [x] 5.5 In the same file, add the employee home-to-visit constraint per design.md's D4: identify each employee's first visit of the day via a self-join `if_not_exists` on "no other same-employee-same-date visit with a strictly earlier start_minutes", then join that visit against `DrivingTimeFact` with `origin_kind="employee"`/`origin_id=employee.id`, with the same Haversine-minute fallback when no fact exists.
- [x] 5.6 Introduce a new per-minute weight constant (replacing `_DISTANCE_WEIGHT_PER_KM`) and an assumed-average-speed constant for the Haversine fallback (D5); pick initial values and note in a code comment that they mirror the previous constant's rough magnitude pending manual re-tuning.
- [x] 5.7 Update or add unit-level verification for the constraint logic: a same-region pair with a computed `DrivingTimeFact` scores using that duration; a pair with no fact scores using the Haversine-minute fallback; an employee's first visit of the day incurs a home-leg cost using the employee-origin fact; a later visit of the day does not double-count the home leg.

## 6. Frontend: Admin Portal "Compute driving times" action

- [x] 6.1 Add `computeRegionDrivingTimes(regionId)` to `frontend/src/api.ts`, calling `POST /regions/{id}/driving-times`.
- [x] 6.2 In `frontend/src/admin-portal/RegionsView.tsx`, add a "Compute driving times" action next to "Re-assign regions" on a region's detail view (per the admin-portal delta spec, this is a per-region action, distinct from "Re-assign regions" which is global): in-progress state while running, a result message on success (e.g. entries computed), and an error message on failure.
- [x] 6.3 Run `npx tsc -b` and confirm the frontend type-checks cleanly.

## 7. End-to-end verification

- [x] 7.1 With a disposable region containing a few real geocoded customer locations and at least one employee scoped to it: trigger "Compute driving times" from the Admin Portal, confirm the result message, and confirm rows exist in `driving_times` for that region — one per ordered pair.
- [x] 7.2 Generate a proposed schedule (existing Manual Assignment / route-optimization flow) covering visits in that region and confirm the solver run succeeds; spot-check that the proposal's total travel score reflects computed driving times rather than straight-line distance where data exists.
- [x] 7.3 Confirm the Haversine fallback path by generating a proposed schedule involving a region (or a multi-region employee's cross-region pair) with no computed driving-time matrix, and confirm the solver still runs and produces a schedule (not an error, not a silently-zero travel cost).
- [x] 7.4 Confirm `openspec validate --strict` passes for the change before archiving.
