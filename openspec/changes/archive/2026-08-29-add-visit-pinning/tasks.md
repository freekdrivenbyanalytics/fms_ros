## 1. Data Model

- [x] 1.1 Add a `pinned` boolean column to `assignments` (default `false`) in `backend/app/models.py`'s `Assignment` model.
- [x] 1.2 Create an Alembic migration adding the `pinned` column (with a server default so existing rows backfill to `false`), with a downgrade that drops it. (`backend/alembic/versions/0005_assignment_pinning.py` — verified `upgrade head` and `downgrade 0004` then re-`upgrade head` both succeed against the dev DB.)

## 2. Backend: Unassign and Pin Endpoints

- [x] 2.1 Add `DELETE /assignments/{service_visit_id}` to `backend/app/main.py`: 404s if the visit has no assignment, otherwise deletes the assignment row, sets the visit's `status` back to `unassigned`, and commits.
- [x] 2.2 Add `PATCH /assignments/{service_visit_id}` accepting `{"pinned": bool}`: 404s if the visit has no assignment, otherwise updates that assignment's `pinned` flag and returns the updated assignment.
- [x] 2.3 Add `pinned` to `AssignmentOut` in `backend/app/schemas.py`, and a small request schema for the pin update body. (`AssignmentPinUpdate`.)

## 3. Backend: Pin-Aware Optimization

- [x] 3.1 Update `backend/app/solver_client.py`'s `build_optimize_payload` to query every service visit (not just unassigned ones) and classify each: no assignment or an unpinned assignment → schedulable `VisitIn`; a pinned assignment → `ExistingAssignmentIn` problem fact (as today). A visit with an unpinned assignment must not appear in both lists.
- [x] 3.2 Update `POST /optimize/apply` in `backend/app/main.py`: for each visit in the proposal's `scheduled` list, look up its current assignment. No assignment → create one (reuse `create_assignment`). Unpinned assignment → update its `employee_id`/`planned_start`/`planned_end` in place. Pinned assignment → add to `skipped_visit_ids` instead of changing it.

## 4. Frontend: Unassign and Pin Controls

- [x] 4.1 Add `pinned: boolean` to the `Assignment` type in `frontend/src/types.ts`.
- [x] 4.2 Add `unassignVisit(serviceVisitId: number)` and `setAssignmentPinned(serviceVisitId: number, pinned: boolean)` to `frontend/src/api.ts` for the two new endpoints. (`unassignVisit` handles the endpoint's 204-no-body response separately from the shared `handleResponse` helper, which assumes a JSON body.)
- [x] 4.3 Add "Unassign" and pin/unpin controls to each assigned visit card in `frontend/src/components/AssignedVisitList.tsx`, showing whether the assignment is currently pinned.
- [x] 4.4 In `frontend/src/App.tsx`, add handlers so: unassigning removes that assignment from state and flips the visit's status back to `unassigned`; pinning/unpinning updates that one assignment in place; and the existing optimize-applied handler upserts by `service_visit_id` (an applied visit may already have an assignment in state) instead of always appending. (`npx tsc --noEmit` passes with no errors.)

## 5. Verification

- [x] 5.1 Pin one assignment from the seed data, run the optimizer, and confirm the proposal leaves that visit's employee/time unchanged while still being free to reshuffle other, unpinned assigned visits. (Pinned visit 12 via `PATCH /assignments/12`; ran `POST /optimize/propose` — visit 12 did not appear in the proposal at all (correctly excluded as a fixed fact), while visits 11/13/14/17/18 (unpinned, already assigned) appeared as candidates and 15/16 remained unschedulable. `GET /assignments` confirmed visit 12's row was untouched afterward.)
- [x] 5.2 Unassign a visit and confirm it moves from the Assigned Visits list to the Unassigned Visits list, and that its assignment (and pin) is gone. (`DELETE /assignments/17` → 204; `GET /service-visits` showed visit 17's status flipped to `unassigned`; `GET /assignments` no longer listed it. A second `DELETE` on the same visit correctly 404s.)
- [x] 5.3 Apply a proposal that moves an existing unpinned assignment to a different employee/time and confirm the assignment is updated in place (no duplicate row, still one assignment per visit). (Applied a proposal moving visit 11's unpinned assignment to a new time; `GET /assignments` count stayed the same (5 rows, no new one for visit 11) with `planned_start`/`planned_end` updated to the new value.)
- [x] 5.4 Generate a proposal, pin one of its visits before applying, then apply and confirm that visit is reported in `skipped_visit_ids` and its (pinned) assignment is unchanged. (Generated a proposal including visit 13 (then-unpinned), pinned visit 13 via `PATCH`, applied the stale proposal: `skipped_visit_ids: [13]`, `created` covered 11/14/17/18. `GET /assignments` confirmed visit 13 kept its original employee/time and `pinned: true`.)
- [x] 5.5 Confirm Day Planning and Customer Portal are unaffected, and that manually assigning a still-unassigned visit via the existing flow still works exactly as before. (Manually assigned visit 16 via `POST /assignments` — 201, correct fields, `pinned: false` by default; a second attempt on the same visit correctly 409s. Re-checked all pre-existing read endpoints (`/employees`, `/service-visits`, `/assignments`, `/regions`, `/skills`, `/customers`, `/customer-locations`, `/contracts`) — all still 200. `npx tsc --noEmit` passes with no errors.)
