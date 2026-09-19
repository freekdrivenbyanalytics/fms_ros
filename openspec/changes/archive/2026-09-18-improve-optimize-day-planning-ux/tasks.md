# Tasks

## 1. Day-planning route map: loading state

- [x] 1.1 Add a `routesLoading` boolean to `DayPlanningView.tsx`, set `true` when a routes fetch starts and `false` in both the success and error paths, and verify by inspection that it can never be `true` at the same time `routes` or `routesError` is stale from a previous day (reset alongside `routesError` at the start of the effect)
- [x] 1.2 Render a loading indicator under "Routes" while `routesLoading` is true, the existing error message when `routesError` is set, and `DayRouteMap` otherwise, and verify in the browser that switching days shows the loading indicator before the map appears (throttle network in devtools if the fetch is too fast to observe)

## 2. Day-planning route map: legend

- [x] 2.1 Add a legend to `DayRouteMap.tsx` listing each `employeeRoute` in `routes.employees` with a color swatch (from `colorForEmployee`) and `employee_name`, and verify in the browser that the legend's colors visually match each route's polyline color for a day with 2+ employees having assignments
- [x] 2.2 Verify an employee with no assignments that day (empty `route`/`stops`) does not appear in the legend, matching `routes.employees`' existing exclusion of employees with nothing to show

## 3. Backend: plan-from-time floor

- [x] 3.1 Add `plan_from_time: str | None = None` to `OptimizeRunOptions` (`backend/app/schemas.py`), documented as an `"HH:MM"` string
- [x] 3.2 In `solver_client.py`, parse `plan_from_time` (when given) to minutes-since-midnight using the same approach as `_minutes_since_midnight`, and in `_employee_day_schedule_payloads`, for the entry whose `date` is today, clamp `start_minutes` to `max(start_minutes, plan_from_minutes)` before building that entry; skip the entry entirely (matching the existing "no resolved schedule" omission) if the clamped `start_minutes` is at or past `end_minutes`
- [x] 3.3 Apply the same clamping in `build_parallel_group_payloads`'s per-group path (`_group_subset`/`_assemble_payload`) so `parallel` execution mode respects `plan_from_time` identically to `single` mode
- [x] 3.4 Unit-test the clamping logic directly (no DB, no HTTP): a `plan_from_time` later than an employee's normal start pushes today's `start_minutes` later; a `plan_from_time` earlier than normal start leaves `start_minutes` unchanged; a `plan_from_time` at or past `end_minutes` omits today's entry for that employee; a future date's entry is never affected by `plan_from_time`

## 4. Frontend: plan-from-time control

- [x] 4.1 Add `plan_from_time?: string` to `OptimizeRunOptions` in `frontend/src/types.ts`
- [x] 4.2 Add a "Plan from" time input to `OptimizeView.tsx` alongside the existing days-ahead/time-limit/execution-mode controls, defaulting to `"08:00"`, and pass it through `proposeOptimization` the same way `execution_mode` already is
- [x] 4.3 Verify in the browser: running a proposal with a "Plan from" time later than 08:00 produces no proposed visit starting before that time today (compare against the same run with the default 08:00), and that a second day in the run (`days_ahead` ≥ 2) is unaffected

## 5. Manual verification

- [x] 5.1 Confirm the default "Plan from" (08:00) run's proposal is unchanged from a run made before this change existed, for the same input (today has no employee whose normal start is before 08:00 in the current dev data, so this should be a no-op)
- [x] 5.2 Confirm the day-planning loading indicator and legend both render correctly together on a day with multiple employees' routes

## 6. Day-planning route map: empty-day default center

- [x] 6.1 Change `DayRouteMap.tsx`'s `DEFAULT_CENTER` (previously roughly central Netherlands, unrelated to this app's actual coverage area) to Oslo, so an empty day (no routes to fit bounds to) doesn't default to a foreign map view; verified in the browser on a day with no assignments
