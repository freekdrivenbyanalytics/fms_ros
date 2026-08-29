## Context

`backend/app/main.py` already has `create_assignment` (manual assign, rejects if the visit is already `assigned`) and the `POST /optimize/propose` / `POST /optimize/apply` pair added by the route-optimization feature. `backend/app/solver_client.py` currently sends every `unassigned` visit as a schedulable `VisitIn` and every row in the `assignments` table as a fixed `ExistingAssignmentIn` problem fact — the solver (`solver/app/domain.py`/`constraints.py`) already has both shapes (`VisitAssignment` planning entity vs. `ExistingAssignmentFact` problem fact); it has no opinion on *why* a given visit falls into one bucket or the other, that classification happens entirely in the backend before the request is built. See proposal.md - Why / What Changes for motivation; see the delta specs for required behavior.

## Goals / Non-Goals

**Goals:**
- Reuse the solver's existing planning-entity/problem-fact split unchanged — only which visits the backend puts in which bucket changes.
- Keep "pinned" scoped to a single assignment's lifecycle so it can never go stale relative to whether the visit is actually assigned.

**Non-Goals:**
- No optimizer preference for leaving an unpinned assignment where it already is (no "stability" soft constraint) — see Risks.
- No re-validation of skills/region/hours at apply time beyond the existing pinned/unpinned check, consistent with route-optimization's already-accepted trust model.
- No bulk pin/unpin action — one visit at a time, matching the granularity of every other action on this page today.

## Decisions

- **`pinned` lives on `assignments`, not on `service_visits`.** Pinning only means something while a visit is assigned, and storing it on the assignment row means unassigning (deleting that row) clears the pin for free — no separate "clear pin on unassign" step to forget. Alternative considered: a `pinned` column on `ServiceVisit` — rejected because it can go stale (a visit could end up marked "pinned" with no assignment to protect) and would need its own clearing logic wired into the unassign path.
- **`DELETE /assignments/{service_visit_id}`** for unassigning. Deletes the assignment row and sets the visit's `status` back to `unassigned`. 404s if the visit has no assignment, mirroring `create_assignment`'s existing style of rejecting invalid state transitions rather than silently no-op'ing.
- **`PATCH /assignments/{service_visit_id}` with body `{"pinned": bool}`** for pinning/unpinning, rather than two separate pin/unpin endpoints. It's a single boolean field on an existing resource; a partial update is the smaller surface. 404s if the visit has no assignment.
- **Solver payload classification flips from "assignment exists?" to "assignment exists and is pinned?".** In `build_optimize_payload`, a service visit becomes a schedulable `VisitIn` (using the same visit-shape mapping as today, independent of any current assignment) unless it has a pinned assignment, in which case that assignment becomes an `ExistingAssignmentIn` problem fact exactly as before. A visit with an unpinned assignment now appears in neither its old "existing assignment" slot nor as a brand-new addition — it simply moves from the facts list to the schedulable list. The solver itself needs no changes.
- **Apply branches on the visit's live state at apply time, not on how the proposal was generated:**
  - No current assignment → create one (reuses `create_assignment`).
  - Current assignment, not pinned → update that assignment's `employee_id`/`planned_start`/`planned_end` in place. This is new logic, not a `create_assignment` call, since that function's contract assumes the visit starts unassigned.
  - Current assignment, pinned → skip, added to `skipped_visit_ids`. This replaces "no longer unassigned" as the sole staleness check: pinning something between propose and apply is now the only way a queued-up proposal can be invalidated for a given visit.
- **No stability bias in the optimizer.** The solver can move an unpinned visit's employee/time even when the improvement is marginal, since nothing in the constraint set rewards "leave it where it is." Accepted for this change (see Risks) — the escape hatch is pinning.

## Risks / Trade-offs

- [Optimizer can churn a perfectly fine unpinned assignment for a marginal score gain] → Mitigation: pin anything the planner wants kept in place. A "prefer the visit's current assignment, all else equal" soft constraint is a reasonable follow-up if this proves annoying in practice, but it's new solver-side scope this change doesn't need.
- [Applying a proposal overwrites an unpinned assignment's employee/time without checking whether a human changed that specific assignment after the proposal was generated] → Accepted, consistent with route-optimization's existing trust model (no re-validation beyond eligibility); pinning is the documented way to protect an assignment from this.
- [Two code paths now write to `assignments` under different rules — `create_assignment` (visit must be unassigned) vs. the new update-in-place apply logic (visit must be assigned and unpinned)] → Kept as two distinct functions rather than unifying them into one dual-purpose function, since their preconditions are opposite and merging them would make both harder to read.

## Migration Plan

1. Add the `pinned` column (migration + model field, default `false`).
2. Add `DELETE /assignments/{service_visit_id}` and `PATCH /assignments/{service_visit_id}`; extend `AssignmentOut` with `pinned`.
3. Update `solver_client.py`'s payload building to classify by pinned-assignment instead of any-assignment, and `POST /optimize/apply` to branch create/update/skip as above.
4. Frontend: add Unassign and Pin/Unpin controls to `AssignedVisitList.tsx`; update `App.tsx`'s state handlers so unassign removes an assignment and flips the visit back to unassigned, pin/unpin updates that one assignment in place, and the optimize-applied handler upserts by `service_visit_id` (an applied visit may already be in the assignments list) instead of always appending.
5. Verify against seed data: pin one assignment and confirm a schedule run leaves it untouched while reshuffling other unpinned assigned visits as needed; unassign a visit and confirm it reappears in Unassigned Visits; apply a proposal that moves an unpinned assignment and confirm it updates in place rather than creating a duplicate row; apply a proposal for a visit pinned after the proposal was generated and confirm it's reported skipped.
6. Rollback: additive column and endpoints; dropping them (migration downgrade) returns to today's behavior where every existing assignment is always fixed and there is no unassign/pin action.
