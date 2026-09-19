# Design

## Context

`backend/app/resco.py` already has an established shape for every synced entity: a `RescoClient` method pair (`create_X`/`update_X`, each a plain `httpx` POST/PATCH against `{base_url}/{entity}` using Basic Auth), a module-level `sync_X(db, obj) -> XRescoSyncResult` that picks create vs. update based on a remembered `resco_*_id` field, catches any exception and returns a `"failed"` result rather than raising, and (for employees/customers/locations) a `sync_all_X`/`sync_Xs_to_resco` bulk variant. `main.py` calls `sync_X` inline, synchronously, right after `db.commit()` in the relevant create/update endpoint, wrapped in its own `try/except` that logs and falls back to a `"failed"` result - so a Resco outage degrades to "every sync shows failed" rather than breaking the endpoint. This change adds one more entity (`Assignment` → Work Order) following that exact shape; see proposal.md for why.

`Assignment`'s primary key is `service_visit_id` (not its own auto-incrementing id), so it needs a new `resco_work_order_id` column, the same role `resco_user_id`/`resco_account_id`/`resco_asset_id`/`resco_product_id` play on their respective models.

Two call sites mutate an assignment's employee/time today: `create_assignment` (`POST /assignments`, also called directly by `apply_optimization` for a visit with no prior assignment) and `apply_optimization`'s inline branch for an existing unpinned assignment being reassigned (mutates `employee_id`/`planned_start`/`planned_end` directly, no shared helper). Both need the new sync hook.

## Goals / Non-Goals

**Goals:**
- Match the existing Resco sync pattern exactly (client method shape, skip-vs-fail semantics, fail-soft on the write it's attached to) rather than introducing a second style.
- One shared `sync_assignment` used by both write paths, not two separate implementations.

**Non-Goals:**
- No bulk "sync all assignments" endpoint - unlike the master-data entities, assignments are created continuously through normal use (apply / manual assign), not backfilled in bulk, and there could be a large volume of historical ones; a bulk resync isn't needed for this change to be useful. Can be added later if a real need shows up.
- No Resco-side deletion/cancellation when an assignment is unassigned (see proposal.md and the added spec requirement) - matches every other entity's delete behavior in this system today.
- No change to `solver/` or the optimizer's own behavior - this is purely a post-write side effect.

## Decisions

**One shared `sync_assignment(db, assignment) -> AssignmentRescoSyncResult` function, called from both `create_assignment` and `apply_optimization`'s reassignment branch.** Mirrors `sync_employee`'s shape; avoids duplicating the create-vs-update-by-remembered-id logic across two call sites which would otherwise drift.

**Work Order fields sent: planned start/end, resource (employee), linked asset (customer location) - not the full visit detail.** Matches the existing pattern's minimalism (e.g. Assets only send a name; Products only send name+number) rather than mapping every field that theoretically exists. A work order needs enough to be schedulable and locatable in Resco; product/skill detail can be added later if the mobile workflow needs it, without a spec change (an ADDED field, not a behavior change).

**Confirmed live against the Resco Cloud org's `$metadata` (task 1.1/1.2): a scheduled visit is two records, not one.** `fs_workorder` (the entity name assumption was correct) holds `name`/`description` and links to the **asset** via `fs_assetid_fs_asset`, but has no start/end/resource fields. The actual booking - `scheduledstart`, `scheduledend`, and the resource link (`resourceid_fs_resource`) - lives on a *child* entity, `fs_workorderschedule`, linked back via `workorderid_fs_workorder`. This is the same parent/work-order + child/booking split Dynamics 365 Field Service uses (there, `msdyn_workorder` + `bookableresourcebooking`); Resco Cloud mirrors it under its own `fs_` names.

**The Work Order's resource is `fs_resource`, not `systemuser` directly - but no new sync is needed for it.** Confirmed live: Resco auto-provisions one `fs_resource` per `systemuser` the moment that user is created (verified against Alice's employee sync - her `fs_resource` record exists, created 3 seconds after her `systemuser`, linked back via `__targetid_id` equal to her `resco_user_id`). So finding an employee's resource is a lookup (`fs_resource?$filter=__targetid_id eq '<resco_user_id>'`), not something this change creates or maintains.

**`Assignment` stores both `resco_work_order_id` and `resco_work_order_schedule_id`, not just one.** (User decision.) Each sync remembers both the parent Work Order's id and its schedule child's id, so every update after the first is a direct id-based PATCH on each - no filter-lookup, no risk of the lookup missing or matching more than one schedule child if Resco's data ever has stray records. This costs one extra stored column relative to every other synced entity's single-id shape, in exchange for update reliability.

**A sync is now up to 4 Resco calls, not 1**: resolve the employee's `fs_resource` id (lookup), create-or-update `fs_workorder` (name/asset), create-or-update `fs_workorderschedule` (time/resource). On a *reassignment* (not a first sync), the work order's own fields (name, asset) don't change - only the schedule child does - so an update-path sync only needs the resource lookup plus the one `fs_workorderschedule` PATCH, not a redundant `fs_workorder` PATCH.

**`planned_start`/`planned_end` are localized to `Europe/Oslo` before being sent to Resco's `Edm.DateTimeOffset` fields.** (User decision.) `Assignment.planned_start`/`planned_end` are naive datetimes - this codebase carries no timezone concept anywhere else (checked: no other datetime this app owns is ever serialized to an external API) - but Resco's schedule fields require an explicit, DST-aware UTC offset. Localized via `zoneinfo.ZoneInfo("Europe/Oslo")` at the point of sending, not stored differently - `planned_start`/`planned_end` remain naive everywhere else in the codebase, this conversion is local to the Resco payload-building code.

## Risks / Trade-offs

**The assumed entity/field names might have been wrong.** → Resolved by making the live `$metadata` check the first implementation task (tasks 1.1/1.2), before writing any payload-building code - confirmed the entity name assumption was right, but also surfaced the two-entity parent/child structure documented above, which the design has now been updated to reflect.

**A reassignment updates the Work Order's resource, which needs to exist in Resco as a Work Order-schedulable resource distinct from a User.** Confirmed: `fs_resource` is that separate entity. → No mitigation needed beyond the lookup described above - Resco auto-provisions the resource, so this system never creates or manages `fs_resource` records itself, only reads the one that already exists for a synced employee.

**The employee's `fs_resource` lookup could itself fail or return zero/multiple results** (e.g. Resco's auto-provisioning behavior changes, or a resource gets deleted independently in Resco). → Treated as an ordinary sync failure: `sync_assignment` catches this the same as any other exception, returning `"failed"` rather than raising - no special-cased handling needed, consistent with the existing fail-soft pattern.
