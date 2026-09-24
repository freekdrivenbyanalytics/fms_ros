# Design

> Current decision (2026-09-23): current status only; audit history is no longer required. Historical audit-blocker notes below are superseded.

## Context

`add-resco-visit-sync` (archived) established the current Work Order push shape: `RescoClient._work_order_payload` (`backend/app/resco.py:219`) sends only `name` and the asset link (`fs_assetid_fs_asset@odata.bind`); `create_work_order_schedule` separately creates a child `fs_workorderschedule` with the actual start/end/resource. That change's own design.md confirmed the entity/field names live against the real Resco org's `$metadata` before writing payload code - it never needed a customer field at the time, so this gap wasn't caught then. A sibling entity already proves the right field name pattern exists: `create_asset` (`resco.py:136`) sends `"customerid_account@odata.bind": f"/account({location.customer.resco_account_id})"` when creating a Resco Asset - high-confidence (not yet confirmed) that `fs_workorder` uses the same literal field name, since "customerid" bound to `account` is a lookup name Dynamics-family schemas typically reuse across many entities.

Assignment completion has no representation anywhere in this system today - `Assignment` has no status column at all, and `ServiceVisit.status` only distinguishes `unassigned`/`assigned` (a different axis: "is someone assigned," not "did the assigned work happen"). `GET /assignments` (`main.py:1543`) returns every assignment ever made with no date bound; the Manual Assignment board's client-side filtering (`App.tsx`) never removes anything once assigned, so the board has been silently accumulating forever.

The `assignments` capability already codifies a deliberate guarantee: overdue visits are never hidden by the board's date-range control (added specifically so nothing falls through the cracks). This change narrows that guarantee for one specific case (overdue *and* confirmed complete) rather than removing it - confirmed with the user after an initial misreading of the request would have removed it entirely.

## Goals / Non-Goals

**Goals:**
- A newly synced Work Order is immediately usable in Resco (has its required customer, ends up scheduled not draft).
- A planner can see, on the board and on the day-planning chart, whether Resco reports a visit done - without needing a scheduled background job this codebase doesn't have yet.
- The board stops accumulating forever: an overdue, completed visit stops cluttering it, but nothing that might still need attention (not yet confirmed done) ever silently disappears.
- A previously synced visit planned before today whose Work Order is currently Scheduled surfaces as unassigned in the portal, with a clear reason so a planner can rebook it. Any other Resco status protects the assignment from this automatic unassignment.
- Nothing is ever actually lost from view - the new all-visits page shows everything, unfiltered, as an escape hatch.

**Non-Goals:**
- No new scheduled-job/cron infrastructure. This codebase has none today; introducing one is a bigger architectural decision than this change should make unilaterally. The status-pull-plus-reconciliation is one manual trigger; a later change can wire it to a real "start of day" job if that turns out to be worth the infrastructure.
- No change to how a Work Order's *schedule* (time/resource) is pushed - only the parent Work Order's own fields (customer, status) and the new read-back path.
- No Resco-side deletion and no marking Work Orders completed from the portal. The portal sets Scheduled on initial creation and, if supported, resets an eligible missed Work Order to an agreed unscheduled status when unassigning it locally. The user confirmed Draft as the reset target (`statecode=0`, `statuscode=1`).
- No visit-history page filtering/search UI beyond a plain list for this change - matching `day-planning`'s stated read-only, no-edit posture, kept simple; richer filtering can follow if it turns out to be needed.

## Decisions

**New Work Orders start Scheduled.** Live verification confirmed the customer binding works, but supplying the customer and schedule child leaves the Work Order in Draft. The portal must explicitly set `statuscode=5` (Scheduled) during initial sync. Routine updates must not overwrite a status subsequently set by field staff.

**Keep Resco status information precise.** Display Resco's formatted status label, and retain the raw state/status information needed for reliable decisions. Completion (`statecode=1`) controls the completed-visit display rule; it does not define eligibility for unassignment. Reconciliation must positively identify Active/Scheduled (`statecode=0`, `statuscode=5`), using a successful fresh read. A missing label, failed read, missing Work Order ID, or merely non-completed status is insufficient.

**Status sync reads Resco; overdue reconciliation unassigns in the portal.** The user-facing action pulls the current status for assigned visits previously synced as Work Orders, using their remembered IDs. Keep the existing manual trigger and perform the portal reconciliation after successful status reads; no background job is introduced. These are distinct operations with different effects: status sync updates local status information, while reconciliation may remove an eligible local assignment and optionally reset its existing Resco Work Order. Show separate counts for status updates, local unassignments, skipped/failed reads, and remote reset failures.

**Only past Scheduled work qualifies for automatic unassignment.** Interpret "assigned yesterday (or any day before today)" as the assignment's planned work date: `assignment.planned_start.date() < today` in the portal's local calendar, not its record-creation time and not the visit's nominal `requested_date`. An assignment planned today or later remains assigned even when its requested date is older. A past assignment qualifies only when its previously synced Work Order is positively confirmed still Scheduled. Any other status, including an in-progress, completed, cancelled, Draft, Ready, or unknown status, leaves the assignment alone. Never-synced assignments and failed status reads also remain assigned. The pin/elapsed-time lock exception applies only to this narrow qualifying set.

**Current status is sufficient (user revision, 2026-09-23).** The user explicitly removed the audit-history requirement. A fresh Active/Scheduled response and planned_start before today qualify, regardless of prior statuses. No audit endpoint is called. The prior audit investigation below is historical, not an implementation dependency. Failed or malformed status reads protect assignments. Durable reset rows survive assignment deletion; retries freshly read status and conditionally PATCH using the returned ETag, cancelling on progress or reuse by an active assignment. Missing ETags defer only the remote reset, not local unassignment.

**Reset the existing Resco Work Order when possible.** After identifying an eligible assignment, the portal removes the local assignment, clears its pin, returns the visit to unassigned, and records the reason. If Resco supports it, also move that same Work Order back to the agreed unscheduled status. The user confirmed Draft (`statecode=0`, `statuscode=1`) as the target. Verify the transition and any schedule-child implications before implementing it. A secondary integration failure must not undo the local unassignment: report a warning and preserve the Work Order ID and enough reset context independently of the deleted assignment to support a retry. Recheck eligibility before a remote reset; do not overwrite work that field staff have since progressed.

**The "never took place" reason lives on `ServiceVisit`, not `Assignment`.** The reconciliation *deletes* the assignment (same as a manual unassign) - a reason column on `Assignment` would vanish with the row it's trying to explain. A nullable `unassigned_reason` column on `ServiceVisit`, set by the reconciliation and cleared whenever that visit is assigned again (manually or via applying a proposed schedule), survives exactly as long as it needs to.

**The board's hide-rule and the new visit-history page both read from the same unfiltered `GET /assignments`/visit-listing data; the hide-rule is enforced client-side.** Matches the existing pattern - the assignment page's date-range control is already a client-side filter over data the backend returns unfiltered (`App.tsx`'s `assignedVisits`/`unassignedVisits` derivation). Changing the backend to filter would mean building a second, parallel "give me everything" endpoint for the visit-history page anyway; simpler to keep one backend shape and add the one extra client-side condition (overdue AND completed → excluded) alongside the date-range filtering the board already does.

**The pin/elapsed-time lock exception is limited to past work that is currently Scheduled.** A qualifying assignment can be unassigned regardless of its stored pin or elapsed-time lock. A past assignment with any other status, no synced Work Order, or an unsuccessful status read remains protected from this reconciliation. Manual pin controls and optimizer locking retain their existing behavior.

**Confirmed live (Resco `$metadata` + behavioral checks): field names and status codes.** `fs_workorder` accepts `customerid_account@odata.bind`. Scheduled is `statecode=0, statuscode=5`; Completed/Closed is `statecode=1, statuscode=2`. The customer and schedule alone do not advance a newly created Work Order from Draft; an explicit Scheduled update is required. Fetch formatted labels with `Prefer: odata.include-annotations="*"`; the returned suffix is `@RescoCloud.FormattedValue`. Completion and Scheduled eligibility are separate predicates.

**Customer, functional location and Asset mapping.** The current mapping supersedes the earlier Account-per-location proposal. One portal Customer maps to one Resco Account and keeps `Customer.resco_account_id`. Each CustomerLocation maps to one `resco_functionallocation`, storing `resco_functional_location_id`, and one Asset storing `resco_asset_id`. The Asset links to its functional location and to the parent customer Account. An assigned visit uses this location's Asset and the parent Account on its Work Order. No Account ID is added to CustomerLocation.

**Names, coordinates and contact ownership.** Name the Account after the portal customer. Name the functional location using the portal location's existing display name (its address); use exactly the same name for its Asset. Store address and coordinates on the functional location, with absent coordinates allowed and later updates supported. Contact name, email, phone, mobile and organization number belong to the parent Account, with any required Resco Contact mapping verified first. Customer edits update this shared Account; all location Assets retain their customer link, so contact data is not duplicated per location. Renames and address edits update remembered remote IDs, never create duplicates by name. Equal location names do not imply equal identity.

**Work Order names identify the visit.** Use `Customer name: address | Visit <service_visit_id>` so repeated visits to the same location are distinguishable. Keep the visit suffix intact when truncating the descriptive prefix to Resco's 160-character limit. Product codes remain available in existing product data; adding them to the name is optional future presentation, not needed for uniqueness. Names are display text, never lookup keys.

**Catch up existing links without duplicates.** Existing customer Account IDs remain active, not legacy. For each location without a functional location ID, create the functional location and save its ID immediately. Reuse its existing Asset ID, update the Asset name and link to the functional location and parent Account. Keep existing Work Order IDs and bind each to its visit's Asset and customer without resetting progress or schedule. Do not delete unrelated Resco records or infer a mapping from names. The discarded per-location Account design was not implemented in this session; there is no automatic conversion/deletion of such Accounts to perform.

## Risks / Trade-offs

### Apply investigation (2026-09-22)

The live OData schema exposes `resco_audit` and `resco_mobileaudit`. Both returned
zero records for verification Work Order `e9bc05e8-cd5d-4ff7-8fde-637b12a4a3e7`,
despite its verified Draft/Scheduled/Completed transitions. The newest organization
audit events (queried by descending createdon) are `Organization Audit Disabled`
(`statuscode=110`, 2026-09-11). Additional test transitions on 2026-09-22 still
produced no audit records. Therefore the current integration cannot establish a
complete status history for this Work Order; an empty audit result is not evidence
that it never progressed. The evidence rule requires a user decision before
implementing automatic unassignment: accept fresh Scheduled status plus locally
observed progress with an explicit between-sync blind spot, or require configured,
complete Resco auditing before enabling reconciliation.

On that same clearly named test Work Order, setting Active/Scheduled and then
Active/Draft succeeded. Its single schedule child retained its status, resource,
start and end unchanged. The original Completed/Closed status was restored after
the check. A Draft reset alone does not remove or clear the schedule child; this
matches the existing non-goal of changing schedule synchronization, but field UI
visibility still needs verification.

The Account schema has emailaddress1 and telephone1, but no contact-name or mobile
field. Contact exposes firstname/lastname/name, emailaddress1, telephone1 and
mobilephone, with parentcustomerid_account; Account exposes primarycontactid_contact.
Implement contact details through a remembered linked Contact, verifying create,
update and clear behavior before coding that payload. The additional remembered
contact ID belongs in the additive schema plan and technical-ID display.

**Draft resets are verified and conditional.** Scheduled-to-Draft leaves the schedule child intact. Resco rejects stale If-Match ETags with HTTP 412 and accepts the current ETag. A conflict retains a pending reset; the next retry freshly reads status and cancels if no longer Scheduled. Previously observed progress is not an eligibility criterion under the revised rule.

**Explain the local reconciliation alongside status sync.** The action should say that it refreshes Resco statuses and unassigns past visits whose Work Orders are currently Scheduled. It must not suggest that every unfinished or unsynced assignment will be removed. Report a failed remote reset separately from a successful local unassignment.

**Narrowing "overdue visits are never hidden" and overriding the elapsed-time lock are both changes to guarantees another part of this system (and its users) may currently depend on.** → Scoped as narrowly as the user specified (only overdue+completed hides; only past planned assignments freshly read as currently Scheduled auto-unassign); the "never hidden" guarantee still holds for every other overdue visit exactly as before. Called out as **BREAKING** in the proposal rather than treated as a minor tweak.

## Migration Plan

1. Alembic migration: `resco_status` (nullable string) on `assignments`; `unassigned_reason` (nullable string) on `service_visits`; `resco_functional_location_id` (nullable string) on `customer_locations`. All additive, no backfill needed (existing rows simply start with neither set).
2. Store raw current status codes on Assignment and durable reset context in resco_draft_resets, independently of the deleted Assignment (migration 0027).
3. Backend Work Order payload/status-pull code lands together with the migration.
4. Frontend changes (status badges, the board's hide rule, the new visit-history page/tab) land in the same change, since they depend on the new fields existing.

## Implementation findings (2026-09-20)

Live behavioral verification used records named `Manual Verify status tracking 2026-09-20`:

- Functional location: `b3e56b5d-ee97-4727-a86f-22e9b935535f`.
- Asset: `706609af-f24a-4f07-bd7b-4b806275885e`.
- Work Order: `e9bc05e8-cd5d-4ff7-8fde-637b12a4a3e7`.
- Schedule child: `cf40e17c-707e-421b-b1d7-cba039571883`.

The Work Order accepted the customer binding and retained it on GET. After creating
its schedule child, it remained `statecode=0` (Active), `statuscode=1` (Draft).
Explicitly PATCHing `statuscode=5` produced Scheduled. Therefore implementation must
explicitly set the scheduled status; supplying the customer and schedule is insufficient.
PATCHing only this verification Work Order to `statecode=1, statuscode=2` returned
Completed/Closed on GET. Formatted labels use the annotation suffix
`@RescoCloud.FormattedValue`. The verification Work Order is left Completed/Closed.

The functional location accepted address fields and coordinates 59.9139, 10.7522;
GET returned both unchanged. The Asset accepted
`resco_functionallocationid_resco_functionallocation@odata.bind`, and GET confirmed
the remembered functional location ID. Metadata confirms address fields
`resco_address_line1`, `resco_address_line2`, `resco_address_line3`,
`resco_address_postalcode`, `resco_address_city`, and `resco_address_country`.
This API check supports the restored functional-location mapping. Task 1.4 still
requires verification in the field-facing view. No application code or local
database records have been changed at this point.

## User clarification (2026-09-20)

The earlier rule "overdue and not completed, including unsynced" is superseded.
Status sync concerns assigned visits with previously synced Resco Work Orders.
Automatic portal unassignment concerns only work planned yesterday or earlier whose
Work Order is currently Scheduled. Any other status is excluded.
A corresponding Resco reset to Draft is desired if supported; the user confirmed
that destination. The clarification does not request a new background job or separate trigger.

The earlier question about button placement distracted from this substantive rule.
Keep the planned bulk action on All Visits, with no per-visit edit actions. When
updating the delta specs, explicitly permit the bulk status-sync/reconciliation action
while keeping individual visit rows read-only.

The proposal, delta specs and tasks are revised alongside this design. No application
code is changed by this planning revision.

## Account granularity verification (2026-09-20)

Live metadata confirms Account coordinates `address1_latitude`/`address1_longitude`,
no direct Asset coordinates, and the optional Asset-to-functional-location relationship.
The user-linked Account `963f786f-5d89-4e4b-a646-650fa40ca99f` is an older record named
`Manual Verify - Customer (updated)` with null coordinates. Its sole Asset,
`76474972-449f-4099-abbe-b255624fbe9d`, has no functional-location link. The recent test
Asset `706609af-f24a-4f07-bd7b-4b806275885e` instead belongs to Account
`cc927703-f123-4294-a48a-03ea9d461f69`. These are different tests; the user's observation
does not disprove the earlier API test. Neither test establishes what the mobile map renders.
The latest design uses functional-location coordinates and the Asset relationship;
the temporary Account-per-location proposal is superseded.


## Customer identity, contacts and follow-up scope (2026-09-22)

The current mapping is Customer -> Account, CustomerLocation -> functional location
plus one same-named Asset. Actual Resco GUIDs remain the update keys and are stored
on their corresponding portal entities. The earlier name-plus-location-ID Account
identifier and per-location Account fan-out are superseded.

Customer email, telephone and mobile already exist in ORM storage; contact-person name
and complete editing support need checking/extension. Keep contact fields editable,
verify Account/Contact mappings, and sync updates and clears to the single customer
Account. Location-specific addresses and coordinates stay on functional locations.
Seed missing demo contacts explicitly and repeatably without overwriting existing values.

**Technical IDs in the portal.** Show full, read-only, copyable Resco IDs using the
Tripletex-ID detail-field convention: Account ID on Customer; Functional Location ID
and Asset ID on CustomerLocation; Work Order ID and schedule ID on assigned-visit
details. Persist and return IDs after each successful remote creation, including partial
syncs; absent IDs remain visibly unset. Update API response schemas and frontend types
with the views. No full remote import is introduced by this bookkeeping requirement.

### Recommended delivery split

Keep this change focused on customer/functional-location/Asset identity, contacts, status sync and overdue
reconciliation. The following requested work is captured here for separate dependent
OpenSpec changes; it is not silently included in this change's implementation checklist.

1. `add-service-order-type-tasks`: reusable portal task masterdata (stable ID, name,
   soft deletion), task CRUD and assigning a task set to a service order type. A task
   can belong to multiple types. The existing relationship remains: each product has
   at most one type; a type may have many products. Include repeatable example seed data.
2. `sync-resco-job-templates-and-skills`: depends on the task change and this change's
   Work Order mapping. Sync portal Skills to Resco, retaining product-skill associations.
   Sync each service order type as one Resco job template with its tasks and no products.
   When syncing an assigned visit, send its applicable template reference(s), actual
   visit product(s), and tasks from those types. Remember external identities so updates
   and retries do not duplicate templates, tasks, skills or Work Order children. Preserve
   field completion/progress when revisiting existing Work Orders.

Examples to carry into the task change:

| Service order type | Tasks |
| --- | --- |
| Generelle vaktmestertjenester | generell inspeksjon; utføre lette reparasjoner; registrere avvik |
| Vaktmestertjenester (vinter) | the same three tasks plus lett snømåking |

The second follow-up needs live schema verification for Resco job templates, template
tasks, skills, Work Order products/tasks and their relationships; these mappings are not
yet established by the existing Account/Work Order checks. Determine whether linking a
job template creates tasks automatically before adding explicit task creation, to avoid
duplicates. The existing portal allows multiple products on one contract line/visit, so
resolve visits whose products have different service order types, missing types, and
shared tasks. Do not assume one product/template per visit or silently drop products.
Also specify which template/task edits affect future versus already-issued Work Orders.


Official setup reference: https://docs.resco.net/wiki/Auditing (server auditing).
Organization auditing is enabled under Admin Console > Settings > Organization > Audit;
Work Order entity auditing is configured under Data > Entities > More Settings > Audit.
Retention must preserve the full interval being evaluated. The current disabled-audit
organization remains eligible for status reads, but not automatic reconciliation.


## Historical implementation progress (2026-09-22; superseded by current revision)

Migration 0026 has been applied: status label/raw codes on Assignment, reason on
ServiceVisit, functional location ID on CustomerLocation, and contact name/Resco
Contact ID on Customer. Status pulls and the All Visits page are implemented, with
per-assignment reconciliation skip reasons. Automatic unassignment is deliberately
not implemented/enabled yet: the complete-history adapter, durable Draft-reset
context, reset retries and positive reconciliation path remain unchecked tasks.
There is no config switch that can bypass missing audit verification.

After the user reported enabling auditing on 2026-09-23, a minimal audit query
returned HTTP 200 with no rows, while ordered and Work Order-filtered audit queries
returned HTTP 500 (Internal server error). Ordinary Work Order reads still succeeded.
The existing clearly named test Work Order eab3ba37-17a7-44d8-98cb-bab5d18adcaf
was changed from Completed to Scheduled and restored to Completed successfully;
the subsequent minimal audit query still returned no rows. Organization enablement
and Work Order field auditing therefore remain unverified through the integration.
Do not infer that auditing is disabled solely from these new responses; inspect
the Admin Console audit settings/logs and resolve audit API access before proceeding.

After the user also enabled Work Order entity auditing, the same test's Scheduled
transition and restoration to Completed succeeded again. Audit reads now returned
HTTP 500 even for `$top=1` and a minimal field selection; the reported message was
only `Internal server error.` One response also contained malformed JSON. This is
an unresolved audit-read failure, not evidence that the user's enablement failed.
Admin Console visibility of the test transitions must be checked to distinguish
recording/storage problems from OData access problems. No real assignments changed.

Account primary-contact binding and clearing all contact fields were verified live
using test Account `0faa91c8-f1d0-4a66-bf4b-d263dfb33407` and Contact
`0a0fa8ee-40f7-4028-985a-fe2a72540dea`. Contact name is sent as lastname with
firstname unset; the portal retains one contact-name field. Existing fields are
reused for email, phone and mobile. `python -m scripts.seed_demo_contacts` filled
missing fields on 150 existing CSV demo customers, with no external push.

End-to-end sync was verified using temporary local DB rows (removed afterwards):
functional locations `b370883e-9f40-4f51-b5f0-cbb13c1e4eba` and
`db049988-f541-4077-b464-4d7bfb008d7a`, with Assets
`49b3d6ee-829c-4933-9847-f728a58d8eac` and
`55abaacb-7077-4deb-aba4-2aa4a61f56b9`. Both Assets had the functional location's
name, their respective coordinates and the same parent Account. Test visit 98314
produced Scheduled Work Order `eab3ba37-17a7-44d8-98cb-bab5d18adcaf` and schedule
`136f317a-5356-4059-a2d4-3cece074a07a`. Resync after marking only this test Work
Order Completed preserved Completed status. Clearly named remote test records remain.

Backend verification: 48 tests pass. Frontend type-check/build passes. Oxlint reports
six existing warnings in unchanged effect/export patterns; the new All Visits view
adds no warning. Field-facing Resco navigation remains unchecked.

On 2026-09-23, headless Edge checks using temporary Playwright and controlled API
fixtures verified that overdue completed visits disappear from Manual Assignment,
remain on All Visits and Day Planning, and retain their full Work Order/schedule IDs.
The All Visits status button issued the expected request and refreshed both views;
no browser page errors occurred. These checks do not substitute for live Resco field
navigation or the live status-button check in task 9.2. Additional backend tests cover
contact-link failure/retry without duplicate Accounts or Contacts, changes and clears,
shared customer links and independent coordinates, duplicate location names, existing
Asset catch-up, and archived/deleted locations and parents. Database filtering fixtures
are rolled back and external sync is mocked.


The live location catch-up completed: 150 synced, 153 skipped for missing prerequisites,
0 failed (303 candidates). No existing remembered Work Orders were eligible for the
binding/name catch-up. Names/bindings were verified by the separate test above.


## Current implementation (2026-09-23)

Current status now drives reconciliation; auditing is not called or required. Migration
0027 adds durable reset rows (Work Order ID, visit ID, schedule ID, planned start,
pending/completed/cancelled state and last error). Local unassignment and the pending
reset are committed together before the best-effort remote reset. The reason states
that the past planned visit is still Scheduled, without claiming it never took place.
Retries re-read status, treat an already-Draft order as complete, cancel progressed or
reassigned orders, and use If-Match to protect concurrent changes. The demo reset
script clears reset rows before deleting visits to preserve its existing reset behavior.

Live conditional-write verification on the existing test Work Order returned 412 for
a stale ETag (status stayed Scheduled) and 200 for the current ETag Draft reset. Its
original Completed status was restored. 61 backend tests pass, including real database
transaction persistence and retry with mocked remote failures. Frontend build and
strict spec validation pass; six pre-existing lint warnings remain.
