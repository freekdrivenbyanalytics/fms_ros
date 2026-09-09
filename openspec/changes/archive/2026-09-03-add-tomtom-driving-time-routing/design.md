## Context

The optimizer is two services: `backend/` (FastAPI) builds a JSON payload per solve request (`app/solver_client.py`) and posts it to `solver/` (a separate Python process running Timefold Solver). `solver/app/domain.py` defines the CP model (`Employee`, `VisitAssignment`, `ExistingAssignmentFact`, `EmployeeDaySchedule`, `Schedule`); `solver/app/constraints.py` scores it, including today's only travel cost: a Haversine-distance soft penalty between every pair of same-employee-same-day visits (and between a visit and an existing fixed assignment). Neither `Employee` nor `VisitAssignment` carries a location identity today — only raw lat/lon — because distance is computed directly from coordinates.

See proposal.md for why straight-line distance is being replaced, and why TomTom rather than HERE. This document covers how the driving-time matrix is computed/stored and how the solver consumes it.

## Goals / Non-Goals

**Goals:**
- Persist a region-scoped, directional driving-time matrix sourced from TomTom: a single static duration per ordered location pair, not conditioned on time of day or day of week.
- Feed it into the existing constraint-stream model as problem facts the solver joins against, following the same pattern as `EmployeeDaySchedule`/`ExistingAssignmentFact`, rather than a Python-side lookup dict.
- Fall back to a distance-based estimate, in the same unit (minutes), for any leg with no computed entry.

**Non-Goals:**
- No time-of-day or day-of-week variation in driving times — one duration per ordered pair, computed once. (An earlier draft of this design considered day-type/time-segment buckets; dropped per the user's decision to keep this simple.)
- No background job queue or async task infrastructure — computation runs synchronously within the triggering HTTP request, per proposal.md.
- No automatic recomputation triggers (region geo-shape edits, location syncs, employee region changes) — manual only, per spec.
- No cross-region matrix precomputation — a multi-region employee's cross-region legs always use the fallback.
- No UI for matrix freshness/history beyond the immediate compute action's result message.
- No change to the Tripletex or Nominatim-geocoding integrations.
- No re-tuning of the existing skill/region/overlap hard constraints — only the travel-cost soft constraints change.

## Decisions

### D1: Driving-time facts are problem facts joined in constraint streams, not a Python dict
Add a `DrivingTimeFact` frozen dataclass (`origin_kind`, `origin_id`, `destination_kind`, `destination_id`, `duration_minutes`) as a new `ProblemFactCollectionProperty` on `Schedule`. Constraints join `VisitAssignment`/`Employee` pairs against it with `Joiners.equal` on the composite key, using `.if_exists`/`.if_not_exists` to select the driving-time path or the fallback path — the same idiom already used for `EmployeeDaySchedule`. Rejected alternative: build a Python dict from the fact list once and capture it in a closure inside `define_constraints`. That works, but constraint streams are built once from `constraint_factory` independent of any particular solution instance, so the dict would have to be rebuilt per solve from the request payload before calling `define_constraints`, coupling constraint construction to request data in a way the current architecture (constraints defined statelessly, facts supplied per-solve) doesn't do anywhere else. Staying consistent with the existing fact/join pattern is simpler to reason about and test.

### D2: Location identity added to the solver payload/domain
`origin_kind`/`destination_kind` distinguish `customer_location` from `employee` because their ids are drawn from separate, potentially overlapping id spaces. `VisitIn`/`VisitAssignment` gain `location_id` (the visit's customer_location_id); `Employee`'s own `id` doubles as its home-location id under `origin_kind="employee"`. `backend/app/solver_client.py`'s `_visit_payload` adds `location_id`; `_employee_payload` needs no change since `id` already serves this purpose.

### D3: Backend resolves and ships only the relevant driving-time facts per solve
`build_optimize_payload` queries `DrivingTime` rows scoped to the regions actually touched by the current candidate visits and employees (not the whole table), and includes them as a new `driving_times` list in the payload — mirroring how `employee_day_schedules` is already scoped to `candidate_dates` rather than sent in full. Keeps payload size proportional to the current solve, not to how many regions have ever had a matrix computed.

### D4: "First visit of the day" identifies the home-to-visit leg
Timefold's constraint streams don't have a built-in "argmin" collector that returns the winning entity itself, so home-to-visit cost is attributed via a self-join: a visit V is that employee's first visit of the day when `if_not_exists` finds no other same-employee-same-date visit with a strictly earlier `start_minutes`. That visit's leg then joins `DrivingTimeFact` with `origin_kind="employee"`/`origin_id=employee.id` as the origin. Ties (two visits with the same earliest `start_minutes`) both qualify as "first" and both get charged the home leg — an accepted edge case, since the CP model already treats simultaneous starts for one employee as infeasible via the existing overlap hard constraint whenever durations are positive.

### D5: Fallback estimate converts Haversine distance to minutes at an assumed average speed
The distance-based fallback (`_visit_distance_km` today) is replaced by a fallback that estimates minutes as `haversine_km / ASSUMED_AVERAGE_SPEED_KMH * 60`, using a new constant (e.g. 40 km/h) rather than mixing a km-based penalty with a minutes-based one. The soft-constraint weight constant (`_DISTANCE_WEIGHT_PER_KM = 10` today) is replaced by a new per-minute weight, tuned by re-running representative schedules and comparing proposals before/after, since minutes and km-weighted-by-10 aren't equivalent magnitudes.

### D6: `DrivingTime` persistence and TomTom integration mirror existing patterns
New table `driving_times` (migration `0012`): `id`, `region_id` (FK `regions.id`, `ondelete="CASCADE"` since entries are meaningless without their region), `origin_kind`, `origin_id`, `destination_kind`, `destination_id`, `duration_minutes`, unique on `(region_id, origin_kind, origin_id, destination_kind, destination_id)`. New `backend/app/tomtom_routing.py` (mirroring `geocoding.py`'s/`tripletex.py`'s isolated-module pattern) exposes `compute_region_driving_times(db, region) -> ComputeSummary`: builds the region's location set (D2's endpoints), calls the TomTom Matrix Routing API v2 once for the region's full location set as both origins and destinations with no departure time specified (TomTom returns a static, non-traffic-adjusted typical travel time in this mode), and upserts the resulting durations — replacing the region's previous entries per spec. TomTom's base URL is a stable constant in the module (no sandbox/prod split, unlike Tripletex); the only new setting is `tomtom_api_key`.

**Obtaining and configuring a TomTom API key.** The product to sign up for is TomTom's **Matrix Routing API (v2)**, part of TomTom's Routing APIs family.
1. Go to `https://developer.tomtom.com` and sign up for a free developer account (or log in if you already have one). Signup puts your account on TomTom's free "Freemium" plan.
2. In the Developer Portal dashboard, create a new app/key (under "My Dashboard" → "My Apps" or "Keys" — TomTom's console names this slightly differently depending on the current UI). The Freemium plan includes TomTom's core products by default, which includes Matrix Routing — before proceeding, confirm "Routing API" / "Matrix Routing" is listed as enabled for the key/app you created; if it isn't shown as included, explicitly add/enable it for that key from the dashboard.
3. Copy the generated API key value.
4. Add it to `backend/.env` (create it from `backend/.env.example` first if you don't already have one) as a new line: `TOMTOM_API_KEY=<your-key>`. `backend/app/config.py`'s `Settings.tomtom_api_key` picks it up the same way `DATABASE_URL` is picked up today. `backend/.env.example` gets a matching placeholder line so the requirement is discoverable for future setup.

### D7: Computation endpoint is synchronous, matching "Re-assign regions"
`POST /regions/{region_id}/driving-times` runs computation inline and returns a summary (entries computed, entries skipped) once done, matching the existing `POST /customer-locations/assign-regions` shape. The frontend's "Compute driving times" button shows an in-progress state for the duration of the request, per the admin-portal delta spec.

## Risks / Trade-offs

- **TomTom per-request origin/destination limits** → TomTom's Matrix Routing API v2 serves small matrices synchronously and larger ones only via an asynchronous submit-then-poll job; a region with enough locations to cross that threshold needs the async flow (or the location set chunked into sub-matrices). Confirm the exact synchronous-size threshold for the configured TomTom plan during implementation and add the async/chunked path if needed; not expected to affect the spec's externally observable behavior. Dropping time-of-day variation means this is now a single call/job per region instead of several, so this risk is much less likely to matter in practice.
- **Row volume** → A region with L locations produces up to `L × (L-1)` rows — one entry per ordered pair, no multiplier. Trivial for Postgres even for large regions. Recomputation (full delete+insert per D6) should still be done in a single transaction to avoid a partially-replaced matrix being read mid-write.
- **Weight re-tuning risk** → Switching the soft-constraint unit from weighted km to weighted minutes changes proposed schedules even where driving-time data is complete. Mitigation: D5's re-tuning pass; call out to the user during `/opsx:apply` if proposed schedules look meaningfully different in manual testing than before this change.
- **No traffic/time-of-day sensitivity** → A static typical travel time doesn't distinguish a rush-hour route from an off-peak one; two routes with identical road distance but very different congestion patterns will score the same. Accepted trade-off per the user's decision to keep this simple; a time-aware version could be added later as a separate change if needed.
- **TomTom API cost is metered (with a free tier)** → Manual-only triggering (no automatic recomputation) bounds cost to deliberate planner action, per proposal.md; dropping the 10x time-bucket multiplier reduces per-computation cost further.
