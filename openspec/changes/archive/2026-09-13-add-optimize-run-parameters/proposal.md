## Why

The optimizer currently has no planner-facing controls: the scheduling window is hardcoded to today and tomorrow, the solver's time budget is a fixed backend setting, and every unscheduled visit is penalized identically regardless of how urgent or important it is. A planner who wants to plan further ahead, trade solve time for quality, or make sure higher-priority work gets scheduled first has no way to do any of that today.

## What Changes

- Add a "days ahead" parameter to a proposed-schedule run (default 2, matching today's hardcoded today+tomorrow window), replacing the hardcoded window in `_is_within_scheduling_window`. Capped at 14 days to keep solver problem size reasonable.
- Add a solver time-budget parameter to a run (default unchanged at 30 seconds), replacing the fixed `solver_time_limit_seconds` setting for that run.
- Add a `priority` field to contract lines (1 = high, 2 = medium, 3 = low; default 2), inherited by every service visit the line generates.
- Change how the solver scores an unscheduled visit: instead of a flat penalty per unscheduled visit, the penalty is weighted so that a priority-1 visit left unscheduled always outweighs any number of priority-2 or priority-3 visits left unscheduled (and likewise priority-2 over priority-3); within the same priority, a visit due sooner outweighs one due later. This only changes which visits get left out when not everything fits — it does not change the existing preference for scheduling more visits over fewer, nor the existing travel-time minimization.
- Add these three parameters (days ahead, time budget, and — indirectly, since it's now visible on contract lines — priority) to the admin UI: run parameters on the Optimize screen, and a priority field on the contract line create/edit form.

## Capabilities

### Modified Capabilities
- `route-optimization`: the scheduling window and solver time budget become per-run parameters instead of fixed values, and the "prefer scheduling more visits" requirement is refined into a priority- and urgency-weighted preference among visits that can't all be scheduled.
- `contracts`: contract lines gain a `priority` field, settable on create and update.
- `service-visits`: a service visit's priority is read through its contract line, the same way duration and required products already are.

## Impact

- `backend/app/solver_client.py`: `build_optimize_payload` and `_is_within_scheduling_window` take a `days_ahead` parameter; `_visit_payload` includes each visit's priority and days-until-due; the request's `time_limit_seconds` becomes caller-supplied instead of always `settings.solver_time_limit_seconds`.
- `backend/app/main.py`: `POST /optimize/propose` accepts a request body with `days_ahead` and `time_limit_seconds` (both optional, defaulting as above).
- `backend/app/models.py` + a new Alembic migration: `ContractLine.priority` (integer, default 2).
- `backend/app/schemas.py`: `priority` added to `ContractLineOut`/`ContractLineCreate`/`ContractLineUpdate` and to `ServiceVisitOut` (read through the contract line, matching duration/products); new request schema for the propose endpoint's parameters.
- `solver/app/schemas.py`, `solver/app/domain.py`, `solver/app/constraints.py`: `VisitIn`/`VisitAssignment` gain `priority` and `days_until_due`; the flat "Unscheduled visit" constraint becomes a priority/urgency-weighted one.
- `frontend/src/components/OptimizeView.tsx`: inputs for days-ahead and time-budget before running.
- `frontend/src/admin-portal/ContractsView.tsx`: a priority field on the contract line form.
- `frontend/src/api.ts`, `frontend/src/types.ts`: updated request/response shapes.
