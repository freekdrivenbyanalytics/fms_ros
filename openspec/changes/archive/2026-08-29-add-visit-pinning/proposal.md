## Why

A planner can currently only move a visit from unassigned to assigned — there's no way to undo a manual assignment, and the optimizer treats every existing assignment as permanently fixed. In practice, planners want to reshuffle: pull a visit back to unassigned, protect a specific assignment they don't want touched, and then let the optimizer re-plan everything else — including visits that already have an assignment — around those protected ones.

## What Changes

- Add an "Unassign" action to each assigned visit in the Manual Assignment tab: removes its assignment and moves the visit back to the Unassigned Visits list.
- Add a "Pin" toggle to each assigned visit in the Manual Assignment tab: a pinned assignment is protected from being changed by the optimizer. Unassigning a visit implicitly clears its pin (there is nothing left to protect).
- Change what the optimizer considers "fixed": a schedule run now only holds **pinned** assignments fixed. Every other visit — unassigned, or assigned but unpinned — becomes a candidate the optimizer may (re)schedule, potentially to a different employee and/or time than it currently has.
- **BREAKING** (behavioral): applying a proposal can now move or overwrite an existing, unpinned assignment's employee/time, not just create new assignments for previously-unassigned visits. A visit that became pinned since the proposal was generated is skipped at apply time, the same way an already-assigned visit is skipped today.

## Capabilities

### New Capabilities

(none — this extends the two capabilities below)

### Modified Capabilities

- `assignments`: add "Unassign an assigned visit" and "Pin/unpin an assigned visit" requirements; the Manual Assignment page requirement gains unassign/pin controls on assigned visit cards.
- `route-optimization`: "A schedule run never alters existing assignments" is replaced by "Only pinned assignments are fixed during a schedule run"; "Generate a proposed schedule" broadens scope to non-pinned assigned visits; "Review and apply a proposed schedule" is replaced by "Applying a proposed schedule creates or updates assignments", so applying can update an existing unpinned assignment in place, and the staleness check for skipping a visit is based on it having become pinned since the proposal was generated, not solely on it being unassigned.

## Impact

- **Backend**: `assignments` table gains a `pinned` column (migration); new `DELETE /assignments/{service_visit_id}` (unassign) and a pin/unpin endpoint; `backend/app/solver_client.py`'s payload building changes to send every non-pinned visit (assigned or not) as a schedulable visit and only pinned assignments as fixed problem facts; `POST /optimize/apply` gains update-in-place logic for visits that already have an unpinned assignment.
- **Frontend**: `AssignedVisitList.tsx` gains Unassign/Pin buttons and a pinned indicator; `api.ts`/`types.ts` gain the new endpoints/fields; `OptimizeView.tsx`'s review table and apply flow are unaffected in shape (still visit → employee → proposed time) but now may include visits that already had an assignment.
- **Solver service**: `solver/app/domain.py`/`constraints.py` are unaffected in structure (a `VisitAssignment` planning entity vs. an `ExistingAssignmentFact` problem fact already exists) — only which category each visit falls into changes, decided by the caller (backend), not the solver.
