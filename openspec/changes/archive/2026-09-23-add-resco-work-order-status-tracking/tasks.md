# Tasks

## 1. Live Resco verification (before writing payload/status code)

- [x] 1.1 Confirm live against the real Resco org that `fs_workorder` accepts a customer binding named `customerid_account@odata.bind` (matching `fs_asset`'s pattern) - create a throwaway test Work Order with this field set (plus its schedule child) and inspect the result
- [x] 1.2 Determine whether adding the customer field alone is sufficient for the Work Order to end up in a non-draft/scheduled state once its schedule child exists, or whether an explicit status field also needs to be set - if the latter, identify the exact field name and the value meaning "scheduled" (via `$metadata` and/or the Resco admin UI)
- [x] 1.3 Identify the field name and exact value(s) Resco's Work Order status uses to mean "completed" - needed for `_is_resco_status_completed` (task 3.3) and confirm it's readable via a GET on `fs_workorder`
- [ ] 1.4 Verify functional-location coordinates and Asset navigation in the field-facing view; verify Scheduled-to-Draft reset and schedule-child effects; investigate status-transition history
  - 2026-09-22: Scheduled-to-Draft API transition verified; schedule child unchanged; test Work Order restored to its original state. Audit API exposed but test transitions have no records and latest organization events report auditing disabled. User confirmed complete audit history is mandatory; field-view verification remains pending; see design.md.
- [x] 1.5 Document findings in this file or design.md if they differ from the assumptions there, before proceeding to task 2 (the field names and status codes in 1.1-1.3 were already confirmed against `$metadata` during proposal; the remaining live checks are behavioural)

## 2. Fix the Work Order push (`backend/app/resco.py`)

- [x] 2.1 Bind Work Order customer to Customer.resco_account_id and Asset to the visited CustomerLocation.resco_asset_id, linked to that location's functional location
- [x] 2.2 Explicitly set new Work Orders Scheduled (statuscode 5) without overwriting progress during updates
- [x] 2.3 Live-verify: sync a real assignment, confirm the resulting Work Order has a customer set and ends up in scheduled (not draft) state in Resco

## 2b. Map customer locations to functional locations and Assets (`backend/app/resco.py`)

- [x] 2b.1 Name Account after Customer; name functional location and Asset identically using the location display name/address; keep Work Order customer/address/visit-ID naming
- [x] 2b.2 Implement functional-location create/update with address and optional resco_latitude/resco_longitude; retain customer-level Account contact sync
- [x] 2b.3 Create/update and remember the functional location before its Asset; reuse existing Account/Asset IDs, link Asset to functional location and parent Account, and preserve Work Order progress
- [x] 2b.4 Live-verify one customer with two locations gives one Account, two functional locations and two same-named Assets, with Work Orders using the correct location Assets

## 3. Schema/model changes (`backend/app/models.py`, Alembic)

- [x] 3.1 Add displayed Resco status and raw status/progress evidence needed to distinguish completion from current-Scheduled eligibility
- [x] 3.2 Add ServiceVisit.unassigned_reason, CustomerLocation.resco_functional_location_id and durable Work Order/reset context surviving assignment deletion
- [x] 3.3 Implement separate completed and current-Scheduled predicates using verified status codes without audit history
- [x] 3.4 Write/run additive migrations for functional-location identity, contact fields as needed, status evidence, reason and reset context; preserve Customer.resco_account_id

## 4. Status pull + overdue reconciliation (`backend/app/resco.py`, `backend/app/main.py`)

- [x] 4.1 Add a `RescoClient` method to fetch a Work Order's current status by its remembered id
- [x] 4.2 Add a bulk function (matching this file's existing `sync_Xs_to_resco` shape) that: for every assignment with a remembered `resco_work_order_id`, fetches and stores its current `resco_status`; for every assignment with no remembered id, skips it (reported as skipped); one failure doesn't block the rest
- [x] 4.3 Reconcile only previously synced assignments with planned_start before today and fresh confirmed current-Scheduled status; unassign locally despite locks, clear pin, set reason, attempt Draft reset and retain retry context. Preserve unsynced, failed-read, progressed and same-day/future assignments
- [x] 4.4 Expose admin status sync/reconciliation with separate counts for pulled statuses, skips, failures, local unassignments and Draft-reset failures
- [x] 4.5 Ensure a visit's `unassigned_reason` is cleared whenever it's assigned again (`create_assignment`, and the reassignment branch in `apply_optimization`)

## 5. Expose new fields in API responses (`backend/app/schemas.py`)

- [x] 5.1 Add `resco_status: str | None` to `AssignmentOut`
- [x] 5.2 Add `unassigned_reason: str | None` to `ServiceVisitOut`

## 6. Frontend: status badges and the board's hide rule (`frontend/src/App.tsx`, `frontend/src/components/AssignedVisitList.tsx`, `frontend/src/components/UnassignedVisitList.tsx`, `frontend/src/components/DayPlanningView.tsx`)

- [x] 6.1 Show `resco_status` on assigned-visit cards (Manual Assignment board) when set
- [x] 6.2 Show `resco_status` on Day Planning timeline blocks when set - Day Planning's own filtering is unaffected (still per-day only; a completed visit still shows, per the day-planning spec delta)
- [x] 6.3 Update the Manual Assignment board's assigned-visit derivation to exclude a visit whose assignment is both overdue (`requested_date` before today) and `resco_status` is completed, alongside the existing date-range filtering
- [x] 6.4 Show `unassigned_reason` on an unassigned visit's card when set

## 7. Frontend: status-pull button and visit-history page

- [x] 7.1 Add the admin bulk Update status from Resco action on All Visits; explain past-Scheduled unassignment and Draft reset, report results and refresh all data
- [x] 7.2 Add a new "All Visits" tab to the Planning portal (`frontend/src/App.tsx`'s view switcher, alongside Manual Assignment/Day Planning/Optimize)
- [x] 7.3 Build the all-visits page: every visit, unassigned and assigned, no date-range filtering, showing each visit's status (including `resco_status` when set) and `unassigned_reason` when set; read-only, no assign/unassign/edit actions, matching day-planning's existing read-only pattern
- [x] 7.4 Wire the new page's data loading (likely reusing the same `listServiceVisits`/`listAssignments` calls `App.tsx` already makes, unfiltered)

## 8. Unit tests

- [x] 8.1 Backend test for `_is_resco_status_completed` covering the confirmed completed value(s) and at least one non-completed value
- [x] 8.2 Test eligibility using planned_start rather than requested_date; protect unsynced, failed pulls, all other statuses, same-day/future visits; accept previously progressed work currently Scheduled; verify pinned past Scheduled unassignment and Draft-reset failure/retry behavior
- [x] 8.3 Backend test confirming `unassigned_reason` is cleared when a visit is assigned again

## 9. Manual verification

- [x] 9.1 Live: sync a real assignment to Resco, confirm the Work Order has a customer and lands in scheduled (not draft) status
- [ ] 9.2 Live: mark that Work Order completed in Resco (or via direct API call, matching how this codebase verifies other live Resco behavior), trigger the status-pull button, confirm `resco_status` updates locally and the badge appears on the card
- [ ] 9.3 Verify a pinned past planned synced Work Order that is currently Scheduled is unassigned in the portal and reset to Draft; verify unsynced and other-status controls remain assigned
- [x] 9.4 Confirm an overdue, completed assignment disappears from the Manual Assignment board but still appears on the new all-visits page
- [x] 9.5 Confirm the Day Planning chart still shows a completed visit's block (with its status), unaffected by the board's hide rule
- [x] 9.6 Run catch-up sync creating missing functional locations and updating existing Asset links/names and portal-linked Work Orders; preserve Accounts, progress and unrelated records
- [x] 9.7 Run the full backend test suite and confirm no regressions

## 10. Mapping, technical IDs and rollout

- [x] 10.1 Update automatic/bulk location syncs for functional location then Asset, preserving customer-level Account sync, dependency skips, Tripletex behavior and local-first warnings
- [x] 10.2 Expose/display actual Resco Account ID on Customer, functional location and Asset IDs on CustomerLocation, and Work Order/schedule IDs on assigned-visit details, read-only and copyable like Tripletex IDs; update API schemas/frontend types
- [x] 10.3 Test one customer/two functional locations, missing/later coordinates, duplicate names, functional-location-success/Asset-failure retry, deleted/archived filtering and existing Asset catch-up
- [x] 10.4 Test repeated-visit name uniqueness and length handling, and ensure normal rescheduling/catch-up never resets progressed Work Orders
- [x] 10.5 Run frontend build/lint and strict OpenSpec validation; document migration and verified reset/history behavior


## 11. Customer identity and contact propagation

- [x] 11.1 Verify customer-to-Account and location-to-functional-location identities, same-named Assets and remembered GUID reuse on rename/resync
- [x] 11.2 Reuse customer email/phone/mobile fields and add missing contact-person name and editing support consistently across model, migrations, API schemas, frontend types and create/detail/edit forms
- [x] 11.3 Verify Resco contact-name/email/telephone/mobile mappings, including whether a linked Contact is needed; sync changes and clears to the parent customer Account
- [x] 11.4 Provide an explicit repeatable CSV or equivalent demo-contact seed that fills missing demo fields without overwriting existing values or automatically syncing external systems
- [x] 11.5 Test customer rename/contact changes and clears on the shared Account, retention of all location Asset links, independent coordinates, and retry without duplicate records
- [ ] 11.6 Live-verify customer contacts, two functional locations with Assets, and all returned technical IDs shown on the appropriate portal details

- [ ] 11.7 Verify ID fields show full technical IDs after sync/reload, an unset state before sync, and retained successful IDs after partial failure

- [x] 11.8 Apply the user revision: use fresh current status without audit history; verify unavailable auditing does not block sync or past-Scheduled reconciliation


## Current implementation boundary

The user removed the audit-history requirement on 2026-09-23. Current status pulls,
past-Scheduled unassignment (including pinned assignments), Draft resets and durable
reset retries are implemented. Migrations 0026 and 0027 are applied. Retry records
survive assignment deletion and recheck current status; conditional ETag writes prevent
overwriting concurrent remote changes. Real Resco rejected a stale ETag with 412,
accepted the current ETag reset, and the test Work Order was restored afterwards.

All 61 backend tests pass, including a database test proving local unassignment and
reset context survive remote failure and a later retry succeeds. Frontend build and
strict OpenSpec validation pass; lint retains six existing warnings. Portal browser
checks with controlled responses passed for tasks 9.4 and 9.5. Remaining live field-view,
status-button and technical-ID visual checks remain unchecked.

Live catch-up: 303 active locations considered; 150 synced, 153 skipped for missing
prerequisites, no failures. End-to-end Work Order behavior was verified separately
with clearly named temporary test records as documented in design.md.

## Archive note (2026-09-23)

Archived at the user's request with 49/54 tasks complete. Tasks 1.4, 9.2, 9.3,
11.6 and 11.7 remain unchecked; archive does not claim these verification steps passed.
