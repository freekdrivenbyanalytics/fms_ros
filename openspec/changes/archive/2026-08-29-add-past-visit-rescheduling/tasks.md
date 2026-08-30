## 1. Backend: Effective Schedule Date

- [x] 1.1 Add an `effective_schedule_date(visit)` helper to `backend/app/solver_client.py` returning `max(visit.requested_date, date.today())`, and use it in `_visit_payload` instead of the raw `requested_date`.
- [x] 1.2 In `backend/app/main.py`'s `propose_optimization`, import and use the same helper when converting the solver's `start_minutes`/`end_minutes` back into real `planned_start`/`planned_end` datetimes, so a rescheduled visit's proposed time lands on today, not its original requested date.

## 2. Backend: Auto-Lock on Elapsed Start

- [x] 2.1 In `backend/app/solver_client.py`'s `build_optimize_payload`, change the fixed-vs-candidate classification so an assignment is treated as fixed (a pinned problem fact) when it's pinned **or** its `planned_start` has already passed, not only when pinned. (`_is_locked()` helper.)
- [x] 2.2 Add a `model_validator` (or equivalent) to `AssignmentOut` in `backend/app/schemas.py` that forces `pinned = True` in the response whenever `planned_start <= now()`, regardless of the stored column's value. (Verified directly: a past `planned_start` forces `pinned: True` even when the stored value is `False`; a future `planned_start` leaves it `False`.)

## 3. Frontend: Show Both Dates

- [x] 3.1 In `frontend/src/components/AssignedVisitList.tsx`, show the visit's requested date alongside the assignment's planned date/time on each card. (Always shown; highlighted with "(rescheduled)" when the planned date differs from the requested date.)
- [x] 3.2 In `frontend/src/components/OptimizeView.tsx`'s review table, show each scheduled visit's requested date alongside its proposed time. (New "Requested" column, highlighted with "(rescheduled)" when it differs from the proposed date. `npx tsc --noEmit` passes with no errors.)

## 4. Verification

- [x] 4.1 Create (or pick from seed data) an unassigned service visit with a `requested_date` before today, run the optimizer, and confirm it can be proposed for today (not the original date) when a feasible employee exists. (Created visit 19 under contract 6 (General Maintenance/North Holland, matches Alice) with `requested_date=2026-08-15`; `POST /optimize/propose` proposed it for `2026-08-29T08:00:00` — today's date — not the original past date.)
- [x] 4.2 Confirm a service visit requested for today or a future date is unaffected — still proposed on its own requested date. (Same run: visits 12/14/18, requested for 2026-09-19/09-03/09-12 respectively, were each proposed on those exact unchanged dates.)
- [x] 4.3 Create an assignment with a `planned_start` in the past (without manually pinning it), run the optimizer, and confirm that visit is not reassigned and the assignment is reported as `pinned: true`. (Manually assigned visit 19 to `2026-08-28T08:00:00` (past, never pinned) — response immediately reported `pinned: true`. A fresh `POST /optimize/propose` did not include visit 19 in `scheduled`, and `GET /assignments` confirmed its row was untouched.)
- [x] 4.4 Unpin that already-started assignment via `PATCH /assignments/{id}` and confirm the request succeeds (200) but the assignment still reports `pinned: true` and is still excluded from a fresh schedule run. (`PATCH /assignments/19` with `{"pinned": false}` → 200, response still showed `pinned: true`; a subsequent `POST /optimize/propose` still excluded visit 19.)
- [x] 4.5 Confirm manually assigning a past-dated service visit via `POST /assignments` still succeeds exactly as before, and confirm a genuinely future/unstarted unpinned assignment is unaffected (still reassignable, still reports its real stored `pinned` value). (Visit 19's manual assignment in 4.3, for a visit requested `2026-08-15`, succeeded normally (201). Visit 12 (planned `2026-09-19`, never pinned) reports `pinned: false` and remained a genuine schedule-run candidate across every propose call in this verification.)
