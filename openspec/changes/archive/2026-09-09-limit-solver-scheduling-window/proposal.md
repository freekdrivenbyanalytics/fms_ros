## Why

`build_optimize_payload` (`backend/app/solver_client.py`) currently sends the solver every schedulable service visit regardless of how far in the future its requested date is — with no scheduling-window filter at all, a visit requested months out is included in every optimization run alongside today's. That inflates the solver's problem size with visits nobody needs proposed yet, and is a direct contributor to slow solver runs. Restricting each run to only today's and tomorrow's visits shrinks the problem to what's actually actionable and is the highest-leverage way to speed up solving, ahead of any solver-tuning changes.

## What Changes

- A proposed schedule run only considers service visits whose effective schedule date (today, if the visit's requested date has already passed, or the requested date otherwise) is today or tomorrow. Visits further out are excluded from the run and reported as unscheduled, the same way visits with unresolved coordinates or no region are today.
- No change to which visits exist, how they're generated, or how `effective_schedule_date` itself is computed — only which visits a given run attempts to schedule.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `route-optimization`: "Generate a proposed schedule" is scoped to visits whose effective schedule date is today or tomorrow; a new requirement documents that visits outside that window are excluded and reported unscheduled, mirroring the existing geocoding/region exclusion requirements.

## Impact

- `backend/app/solver_client.py`: `build_optimize_payload` filters candidate visits to `effective_schedule_date(v) in {today, tomorrow}` before building the payload; visits excluded for being outside the window are added to `excluded_visit_ids` alongside the existing ungeocoded/regionless exclusions.
- No change to `solver/` — the solver itself already only ever sees whatever visits the backend sends it; this change is entirely about what the backend sends.
