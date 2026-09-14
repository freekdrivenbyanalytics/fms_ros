## Why

The existing `reset_demo_data.py` script is a heavyweight, destructive operation that wipes and recreates ~150 Tripletex customers — appropriate for rebuilding the whole demo scenario, but far too much just to make an already-seeded demo usable again after time has passed (all its service visit dates end up in the past, and prior demo/test runs leave a pile of assignments in place). There's no quick, safe way to refresh just the scheduling-relevant state — visit dates and assignments — without touching Tripletex at all.

## What Changes

- Add a new, local-only action a planner can trigger from the Admin Portal that:
  - Shifts every service visit's `requested_date` forward by the same number of days, just enough so the earliest one becomes today — preserving each contract line's visit cadence/spacing relative to the others. If the earliest visit is already today or later, dates are left unchanged.
  - Clears every assignment (including pinned ones), returning every service visit to unassigned.
- No Tripletex API calls, no customer/contract data changes — this only touches service visit dates and assignments.

## Capabilities

### New Capabilities
- `demo-schedule-refresh`: a local-only action that shifts service visit dates forward to start from today and clears all assignments, so a stale demo/test dataset becomes immediately usable again without re-running the full Tripletex reset.

## Impact

- `backend/app/main.py`: new endpoint (e.g. `POST /demo/refresh-schedule`) performing the date shift and assignment clear in one transaction.
- `frontend/src/admin-portal/`: a new small view/button (e.g. under a new "Demo" entry in the Admin Portal nav) that triggers the action with an inline confirmation step.
- No changes to `backend/app/reset_demo_data.py` or the existing `demo-data-reset` capability — this is a separate, much narrower operation.
