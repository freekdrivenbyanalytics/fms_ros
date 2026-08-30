## Context

`backend/app/solver_client.py`'s `build_optimize_payload` currently sends each candidate visit's raw `ServiceVisit.requested_date` to the solver, and classifies a visit as fixed (a problem fact, not a candidate) only when its assignment's stored `pinned` flag is true. `backend/app/main.py`'s `propose_optimization` converts the solver's minute-offset response back into real `planned_start`/`planned_end` datetimes using that same `requested_date`. The solver's own domain model (`solver/app/domain.py`) treats a visit's date as a fixed, non-searchable field — only time-of-day (`start_minutes`) is a planning variable. See proposal.md - Why for motivation; see the delta specs for required behavior.

## Goals / Non-Goals

**Goals:**
- Make "which date a visit lands on" purely a backend value-computation concern, so the solver's domain model and constraints need no changes at all.
- Reuse the existing `pinned` mechanism for the auto-lock behavior rather than introducing a parallel concept, so route-optimization's "only pinned assignments are fixed" rule keeps working unchanged.

**Non-Goals:**
- No multi-day scheduling horizon (per the confirmed decision, a passed requested date always maps to today, never "today or later, whichever is best").
- No backend enforcement preventing manual unpin/unassign on an already-started assignment — per the confirmed decision, manual override stays available; only the optimizer treats it as fixed.
- No change to how travel distance, skills, region, or working-hours constraints work — this only affects which date is used and which visits are excluded as fixed.

## Decisions

- **A visit's "effective schedule date" is `max(requested_date, today)`, computed once per request in the backend.** `_visit_payload` in `solver_client.py` sends this instead of the raw `requested_date`; `propose_optimization` in `main.py` uses the same computation when turning the solver's `start_minutes`/`end_minutes` back into real datetimes. Both call a single shared helper (`effective_schedule_date(visit)`, added to `solver_client.py` and imported by `main.py`) so the two can't drift out of sync. The solver itself is untouched — it still just sees one fixed date per visit and searches time-of-day only, exactly as before this change.
- **"Started" is a full datetime comparison (`planned_start <= now()`), not date-only** — unlike the effective-schedule-date computation above, which is date-only. These are different questions: "has this visit's original date already gone by" (date-granularity, matches how the rest of the app reasons about dates) versus "has this specific assignment's moment already arrived" (needs to be precise, since a visit assigned for later today must not be treated as already started just because it's "today").
- **The auto-lock is computed at read time, not persisted.** `AssignmentOut` gains a `model_validator` that forces `pinned = True` in the response whenever `planned_start <= now()`, regardless of the stored column. `build_optimize_payload`'s classification is updated the same way: an assignment is a fixed fact if `assignment.pinned or assignment.planned_start <= datetime.now()`. Alternative considered: a background job (or a write-on-read side effect) that flips the stored `pinned` column to `true` once an assignment starts — rejected as unnecessary machinery for a value that's cheap to compute on every read and never needs to be "unset" by anything other than time itself.
- **Unpinning an already-started assignment still writes to the stored column and still returns 200**, per the confirmed decision that manual actions aren't rejected. The response (and any subsequent read) still reports `pinned: true` because the computed lock doesn't depend on the stored value once elapsed — this is spelled out as its own scenario in the assignments delta so the behavior is a documented contract, not just an accidental side effect of the implementation.
- **No new field for "planned date."** A visit's requested date (`ServiceVisitOut.requested_date`) and an assignment's actual date (`AssignmentOut.planned_start`) are already both present in every response that includes them together (`AssignmentOut`, `ProposedAssignmentOut` each embed `service_visit`). "Recording and showing both dates" is satisfied by never overwriting `requested_date` (already true — nothing about this change touches that column) and by the frontend displaying both values it already receives. Alternative considered: add an explicit `planned_date` field to the API response — rejected as redundant with `planned_start`'s date component.

## Risks / Trade-offs

- [A visit assigned for later today (not yet started) versus one that started ten minutes ago aren't visually distinguished from a *manually* pinned one — all read as `pinned: true`] → Accepted per the confirmed decision to reuse the same flag; the assignments delta's new requirement documents this as intended, not a bug. A future change could add a separate "why is this locked" indicator if this proves confusing in practice.
- [Computing "started" from the backend server's clock means a manual clock skew or the dev machine's clock being wrong could mis-classify an assignment] → Accepted; every other time-sensitive check in this app (e.g. "today" for effective scheduling date) already trusts the backend server's clock, so this is consistent rather than a new exposure.

## Migration Plan

1. Add `effective_schedule_date(visit)` to `solver_client.py` and use it in `_visit_payload` instead of the raw `requested_date`.
2. Use the same helper in `main.py`'s `propose_optimization` when reconstructing `planned_start`/`planned_end` from the solver's response.
3. Change `build_optimize_payload`'s fixed-vs-candidate classification from `assignment.pinned` to `assignment.pinned or assignment.planned_start <= datetime.now()`.
4. Add a `model_validator` to `AssignmentOut` that forces `pinned = True` once `planned_start <= now()`.
5. Frontend: show the visit's requested date alongside the assignment's planned date/time in `AssignedVisitList.tsx` and in `OptimizeView.tsx`'s review table.
6. Verify: a visit requested for a past date gets proposed for today (not the original date) when otherwise feasible; an assignment whose planned start has elapsed is reported as pinned and excluded from a fresh schedule run even if never manually pinned; unpinning such an assignment succeeds but it's still reported as pinned; manually assigning a past-dated visit is unaffected; a visit requested for today or later is unaffected.
7. Rollback: revert the date computation and the `pinned`-vs-started classification; additive-only, no schema or solver changes to unwind.
