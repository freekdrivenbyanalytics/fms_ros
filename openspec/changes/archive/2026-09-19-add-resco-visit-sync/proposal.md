# Proposal

## Why

Resco (the field service mobile CRM technicians use) already knows about fms_ros's employees (as Users), customers (as Accounts), customer locations (as Assets), and products - but not about scheduled work. A technician currently has no way to see their planned visits inside Resco; someone would have to re-enter each one by hand. Pushing a scheduled visit to Resco as a Work Order, the moment it's scheduled, closes that gap the same way the existing master-data syncs already do for employees/customers/locations/products.

## What Changes

- A scheduled visit (an `Assignment`) is pushed to Resco as a Work Order, automatically, at the moment it's scheduled or rescheduled: when a proposed schedule is applied (`POST /optimize/apply`) and when a visit is manually assigned (`POST /assignments`) — both today's two paths that create or move an assignment's employee/time.
- Following the same idempotent create-or-update pattern already used for employees/customers/locations/products: a remembered Resco Work Order ID is stored on the assignment; a first sync creates the Work Order, a later sync (a reassignment) updates that same record rather than creating a duplicate.
- Following the same skip-not-fail pattern already established: an assignment whose employee or customer location hasn't itself been synced to Resco yet (no remembered Resco User ID / Asset ID) is skipped, reported as such, and does not block the assignment from being created or block other assignments in the same apply from syncing.
- A sync failure (Resco unreachable, an error response) never fails or rolls back the assignment create/update itself - matching every existing Resco sync in this system.
- Unassigning a visit does **not** delete or cancel its Resco Work Order - matching the existing precedent that deleting an employee/customer/product in fms_ros doesn't delete its Resco counterpart either. Out of scope for this change.

## Capabilities

### Modified Capabilities
- `resco-integration`: adds "Assignments are synced to Resco as Work Orders," following the same auto-sync-on-write, skip-if-unsynced-dependency, and fail-soft patterns already specified for employees/customers/customer locations/products.

## Impact

- **Affected code**: `backend/app/resco.py` (new `sync_assignment`/Work Order client methods), `backend/app/models.py` (`Assignment.resco_work_order_id`), a new Alembic migration, `backend/app/schemas.py` (`AssignmentRescoSyncResult`, `AssignmentOut.resco_sync`), `backend/app/main.py` (hook into `create_assignment` and `apply_optimization`'s reassignment branch).
- **Affected systems**: Resco Cloud, via its existing OData-style REST API (same `RescoClient` base already used for User/Account/Asset/Product).
- **Open/unconfirmed detail carried into design.md**: the exact Resco entity logical name and field names for a Work Order are not yet confirmed against the live Resco Cloud org (the existing code covers `systemuser`/`account`/`fs_asset`/`product`, none of which reveal the Work Order schema). This change proceeds on a stated assumption (`fs_workorder`, following the existing `fs_` naming convention) with an explicit live-verification step early in implementation, the same way this project has previously investigated an external integration point live rather than assumed it (e.g. the currently-implemented `add-parallel-region-solving` change's Timefold licensing investigation).
- **Dependencies**: none on other in-flight changes.
