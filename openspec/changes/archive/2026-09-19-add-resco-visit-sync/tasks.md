# Tasks

## 1. Live verification (before building the real payload)

- [x] 1.1 Against the live Resco Cloud org, confirm the Work Order entity's logical name (assumed `fs_workorder`) via the API's `$metadata` endpoint or Woodford's entity designer
- [x] 1.2 Confirm the field names for scheduled start, scheduled end, the linked resource (and whether it binds directly to the existing `systemuser` record or a separate bookable-resource entity), and the linked asset, updating the assumptions in design.md if they differ — **found live**: a scheduled visit is two records (`fs_workorder` parent holding name/asset, `fs_workorderschedule` child holding scheduledstart/scheduledend/resource), and the resource is a separate `fs_resource` entity auto-provisioned per `systemuser` (found via `$filter=__targetid_id eq '<resco_user_id>'`) — design.md updated accordingly

## 2. Data model

- [x] 2.1 Add `resco_work_order_id: str | None` and `resco_work_order_schedule_id: str | None` to the `Assignment` model (`backend/app/models.py`)
- [x] 2.2 Add an Alembic migration for the two new columns, following the existing `resco_*_id` column migrations' shape (e.g. `0015_employee_resco_fields.py`), and verify `alembic upgrade head` applies cleanly against the dev database
- [x] 2.3 Add `AssignmentRescoSyncResult` (`status: "synced" | "skipped" | "failed"`, `detail: str | None`) to `backend/app/schemas.py`, matching `EmployeeRescoSyncResult`'s shape, and add `resco_sync: AssignmentRescoSyncResult | None = None` to `AssignmentOut`

## 3. Resco client and sync function

- [x] 3.1 Add a `find_resource_by_user_id` (or similar) lookup method to `RescoClient`: `GET fs_resource?$filter=__targetid_id eq '<resco_user_id>'`, returning the single matching resource's id (raise `RescoApiError` on zero or multiple matches, matching the "treat as an ordinary sync failure" decision in design.md)
- [x] 3.2 Add a `create_work_order` method to `RescoClient` for the `fs_workorder` parent (name, `fs_assetid_fs_asset@odata.bind`) - no `update_work_order` needed, since a work order's asset/customer is fixed to its (immutable) visit and never changes across a reassignment - and `create_work_order_schedule`/`update_work_order_schedule` for the `fs_workorderschedule` child (`scheduledstart`, `scheduledend`, `resourceid_fs_resource@odata.bind`, `workorderid_fs_workorder@odata.bind` on create), following the existing method pairs' shape (Basic Auth, `httpx.Client(timeout=10.0)`, raise `RescoApiError` on a 4xx/5xx response); localize `planned_start`/`planned_end` to `Europe/Oslo` via `zoneinfo` before formatting for these `Edm.DateTimeOffset` fields (see design.md - this codebase's datetimes are otherwise naive)
- [x] 3.3 Add `sync_assignment(db, assignment) -> AssignmentRescoSyncResult`: skip (not fail) when the assignment's employee has no `resco_user_id` or the visit's customer location has no `resco_asset_id`, reporting which is missing; otherwise resolve the employee's `fs_resource` id, create-or-update the `fs_workorder` (only on first sync - reassignment doesn't change name/asset) and create-or-update the `fs_workorderschedule`, remembering both returned ids on create, and catch any exception into a `"failed"` result - matching `sync_employee`'s shape exactly

## 4. Wire the sync into both write paths

- [x] 4.1 Call `sync_assignment` from `create_assignment` (`backend/app/main.py`) after `db.commit()`, wrapped in the same log-and-fall-back-to-failed `try/except` pattern used in `create_employee`/`update_employee`, and include the result in the response
- [x] 4.2 Call `sync_assignment` from `apply_optimization`'s reassignment branch (the existing unpinned-assignment-moved path) after its own `db.commit()`, the same way
- [x] 4.3 Verify by inspection that `apply_optimization`'s brand-new-assignment path (which calls `create_assignment` directly) picks up the sync automatically from task 4.1 without a second explicit call

## 5. Manual verification

- [x] 5.1 Manually assign a visit whose employee and customer location are both already synced to Resco; confirm a new Work Order appears in Resco with the correct schedule, resource, and asset
- [x] 5.2 Apply a proposed schedule covering both a brand-new assignment and a reassignment of an existing unpinned one; confirm both produce/update a Work Order in Resco (a create for the new one, an update - not a duplicate - for the reassigned one)
- [x] 5.3 Manually assign a visit whose employee has not yet been synced to Resco (no `resco_user_id`); confirm the assignment is still created, its Resco sync is reported as skipped, and no Resco call is made
- [x] 5.4 Stop the Resco integration from succeeding (e.g. temporarily point `resco_base_url` at an unreachable address) and manually assign a visit; confirm the assignment is still created and its sync is reported as failed, without the assignment request itself failing
- [x] 5.5 Unassign a previously-synced visit; confirm no Resco call is made and the Work Order in Resco is left untouched
