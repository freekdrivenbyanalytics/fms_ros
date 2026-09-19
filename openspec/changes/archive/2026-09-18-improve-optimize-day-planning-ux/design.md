# Design

## Context

`DayPlanningView.tsx` fetches routes via `getDayPlanningRoutes(date)` into a `routes` state that starts `null` and has no separate "is fetching" flag — nothing renders under "Routes" until the promise resolves or rejects. `DayRouteMap.tsx` already gives each employee a stable color via `colorForEmployee` (keyed by employee id, from a fixed `ROUTE_COLORS` palette) but never surfaces that mapping outside of a per-marker popup.

`backend/app/solver_client.py`'s `_employee_day_schedule_payloads` resolves one `(start_minutes, end_minutes)` window per `(employee, date)` via `resolve_employee_schedule`, unchanged for every date in the run. `OptimizeRunOptions` (`backend/app/schemas.py`) already carries `days_ahead`, `time_limit_seconds`, and (from the currently-implemented `add-parallel-region-solving` change) `execution_mode` - this adds a sibling field, `plan_from_time`, to the same request/response plumbing (`OptimizeView.tsx` → `api.ts` → `main.py`'s `/optimize/propose` → `solver_client.py`).

## Goals / Non-Goals

**Goals:**
- Minimal, additive changes to existing components/functions - no new files needed for the UX fixes.
- The start-from floor only ever pushes today's earliest proposable time later, never earlier than an employee's own resolved start (see proposal.md).

**Non-Goals:**
- No change to how routes or day-planning assignments are fetched/rendered otherwise - only the loading and legend gaps.
- No change to which employees appear in day-planning generally - the legend mirrors whatever `DayRouteMap` already renders.

## Decisions

**Loading state lives in `DayPlanningView`, not `DayRouteMap`.** `DayPlanningView` already owns the fetch (`useEffect` calling `getDayPlanningRoutes`); adding a `routesLoading` boolean there (set `true` before the fetch, `false` in both `.then` and `.catch`) keeps `DayRouteMap` a pure "render these routes" component and avoids threading fetch state into it. The "Routes" section renders a loading message when `routesLoading` is true, the existing error message when `routesError` is set, and `DayRouteMap` once `routes` is populated - mutually exclusive, matching the existing `routesError && ...` / `routes && ...` pattern already in the JSX.

**Legend lives in `DayRouteMap`, derived from the same `routes` prop it already renders.** It needs no new data: for each `employeeRoute` in `routes.employees`, show `colorForEmployee(employeeRoute.employee_id)` next to `employeeRoute.employee_name`. Rendered as a small row of swatch+name pairs under the map, reusing the color function so the legend can never drift from the map's actual colors.

**The start-from floor is applied at payload-build time, not as a solver-side concept.** `_employee_day_schedule_payloads` already computes `(start_minutes, end_minutes)` per `(employee, date)`; when the target date is today and a `plan_from_time` is given, clamp that date's `start_minutes` to `max(start_minutes, plan_from_minutes)` before building the payload entry. This keeps the solver itself unaware of "now" or floors - it only ever sees a working-hours window, exactly as it does today - so no change to `solver/app/*` is needed, matching this project's established pattern of keeping the solver a pure function of its input payload (see the currently-implemented `add-parallel-region-solving` change's design.md for the same principle). If the floor pushes `start_minutes` to or past `end_minutes` (an employee whose entire remaining day is before the floor), that employee simply gets no `employee_day_schedule` entry for today - identical in effect to today's existing "no resolved schedule that date" path, which the solver already treats as unavailable that day.

**`plan_from_time` is a `"HH:MM"` string, parsed backend-side, not a raw minutes integer.** Matches how the frontend already renders/edits time (`<input type="time">` values are `"HH:MM"`), avoiding a client-side minutes conversion; the backend already converts `time` objects to minutes-since-midnight via `_minutes_since_midnight` for the exact same purpose elsewhere in `solver_client.py`.

## Risks / Trade-offs

**A `plan_from_time` later than every employee's working-hours end today silently leaves today fully unplanned**, rather than erroring. → Matches the existing "no schedule that day" precedent (an employee with an unresolved schedule is silently excluded, not an error) and the spec's own "no scenario without a match" allowance - a planner who sets 18:00 when everyone's day ends at 17:00 gets zero visits proposed for today, same as if no one had a schedule.

**The legend can grow long with many employees on a busy day.** → Out of scope to solve further here (e.g. no scroll/collapse behavior); the existing route-color palette already cycles at 8 colors (`ROUTE_COLORS.length`), so a legend beyond 8 employees already has repeated colors - a pre-existing limitation this change doesn't newly introduce or need to fix.
