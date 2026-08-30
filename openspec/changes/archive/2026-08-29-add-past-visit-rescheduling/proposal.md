## Why

A service visit whose requested date has already passed isn't lost — it still needs doing, just not on that original date. Today the optimizer can't propose anything for it at all in a sensible way (it would either try to schedule it on a date that's already gone, or be excluded outright). It should instead reschedule such a visit to today, while the planner can still see what date it was originally requested for. Separately, once an assignment's planned start time has actually elapsed, reality has already happened — the optimizer must never move it, whether or not a planner remembered to pin it.

## What Changes

- A schedule run (`POST /optimize/propose`) treats a candidate visit's requested date as its own date if that date hasn't passed yet, or as today if it has — never a date that's already gone. This needs no change to the solver itself: the backend simply computes and sends this "effective schedule date" instead of the raw requested date.
- An assignment automatically becomes pinned once its planned start time has elapsed, regardless of whether a planner ever pinned it. This reuses the existing pinned flag/mechanism (shown as pinned, excluded from schedule runs) rather than introducing a separate state; unpinning such an assignment updates the stored flag but does not un-lock it, since the lock is based on elapsed time, not the flag.
- The planner can already see a service visit's original requested date (`ServiceVisitOut.requested_date`) and an assignment's actual planned date/time (`AssignmentOut.planned_start`) via the existing API — no new field is needed to "record" both. What's missing is showing them together: the Assigned Visits list and the Optimize review table currently don't surface the visit's requested date next to its planned date, which matters now that the two can genuinely differ.
- Manually assigning a visit (`POST /assignments`) remains unrestricted for past dates, exactly as today.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `route-optimization`: "Proposed schedule keeps each visit's requested date" is replaced by "Proposed schedule keeps each visit's effective schedule date" (requested date, or today if that's passed); "Only pinned assignments are fixed during a schedule run" gains a scenario covering an already-started (auto-locked) assignment.
- `assignments`: adds "An assignment locks automatically once it has started".

## Impact

- **Backend**: `backend/app/solver_client.py` computes each candidate visit's effective schedule date (`max(requested_date, today)`) instead of sending the raw `requested_date`, and classifies an assignment as fixed (a pinned problem fact) when it's pinned *or* already started; `backend/app/main.py`'s `propose_optimization` uses the same effective-date logic when converting the solver's minute-offsets back into real `planned_start`/`planned_end` values. `backend/app/schemas.py`'s `AssignmentOut` reports `pinned: true` once an assignment's planned start has elapsed, even if the stored flag is `false`.
- **Solver service**: no change — it still receives one fixed date per visit and searches only time-of-day, exactly as today.
- **Frontend**: `AssignedVisitList.tsx` and `OptimizeView.tsx` show a visit's requested date alongside its planned date/time (derived from data the API already returns), most visibly when the two differ.
