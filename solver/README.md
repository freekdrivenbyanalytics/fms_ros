# Solver service

A standalone FastAPI service that wraps [Timefold Solver](https://timefold.ai) to propose an
employee/visit schedule. See the root `README.md` for how to run it locally.

## How the optimizer works

### It optimizes the whole problem jointly, not greedily

Every solve considers all candidate visits and all employees at once — one `Schedule` containing
everyone (`app/solve.py`'s `_build_schedule`) — not "employee 1 picks their day, then employee 2
picks theirs," and not "visit 1 gets assigned, then visit 2." Timefold first runs a construction
heuristic to build an initial solution, then a local-search metaheuristic that repeatedly tries
reassigning a visit's employee or start time and keeps changes that improve the overall score.
For a realistic day (dozens of visits, several employees, 15-minute start-time granularity) the
number of possible schedules is astronomically large, so this is a heuristic search within a time
budget (`time_limit_seconds`, see `solve_schedule`) — it finds a *good* schedule, not provably
*the* best one.

### Scoring is lexicographic: hard, then medium, then soft

All constraints live in `app/constraints.py`, in three tiers that are compared in strict order —
a solution is never allowed to trade a worse tier for a better one:

1. **Hard** (must be satisfied): correct product/skill, correct region, within working hours, no
   time overlap between an employee's visits, and enough gap between consecutive visits to
   actually drive there (see the six "driving time gap" constraints).
2. **Medium**: one penalty point per *unscheduled* visit. This is what drives "schedule as many
   visits as possible."
3. **Soft**: total driving time across everyone's day (see below).

Because medium strictly outranks soft, **the solver always prefers scheduling one more visit over
saving travel time** — a solution with one extra visit scheduled beats a tighter, more efficient
solution that leaves a visit unassigned, no matter how much worse its total mileage is. So a
technician's day can absolutely end up mixing a far-away customer with nearby ones: travel-time
minimization only breaks ties among solutions that already schedule the same number of visits. It
never causes a visit to be dropped just because it's inconveniently located, unless dropping it is
the only way to fit something else in.

### "Minimize travel time" isn't real route optimization

The soft score doesn't sequence a route (no TSP-style path). It's the **sum of pairwise driving
time between every pair of that employee's same-day visits**, plus the home-to-first-visit leg —
see the comment above `_TIME_WEIGHT_PER_MINUTE` in `app/constraints.py`. That's a proxy for
"keep the day spatially clustered," not literal route optimization, so even the soft-score
minimum found isn't necessarily the shortest possible driving loop — just a day where visits tend
to be close together overall.

### Driving time comes from a precomputed matrix, with a distance-based fallback

`DrivingTimeFact` entries are a region's precomputed TomTom driving-time matrix (see
`backend/app/tomtom_routing.py`). When no matrix entry covers a leg — not yet computed, or a
cross-region leg for an employee scoped to multiple regions — the constraints fall back to a
Haversine-distance estimate (`_haversine_fallback_minutes`, assuming 40 km/h) so travel time is
never treated as free.
