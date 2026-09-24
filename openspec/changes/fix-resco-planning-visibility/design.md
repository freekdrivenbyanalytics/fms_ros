# Design

## Context

See proposal.md for motivation. The user confirmed that the missing bookings are on Resco's planning screen. The manually created Magnus Hognas records are comparison references, not records to import into fms_ros.

The archived `2026-09-19-add-resco-visit-sync` design established separate Work Order and schedule records, remembered IDs and Oslo localization. The archived `2026-09-23-add-resco-work-order-status-tracking` design deliberately keeps status pulls on demand and couples that explicit action to overdue reconciliation. Preserve on-demand operation; the user revision separates status reads from reconciliation into two explicit actions.

Read-only live inspection on 2026-09-24 found:

| Field | Magnus manual reference | Portal visit 97888 |
|---|---|---|
| Work Order ID | 872ff2c1-2785-4f9d-9f82-873ea4c4dba3 | 4f450579-8fdf-4217-a94d-e405b3a7a71f |
| Schedule ID | c7c9452f-9cca-47f1-859e-43caf9a504bb | 07089859-ae9d-46e9-8ae3-f8d2e5e40a4c |
| Work Order name | test-ordre med asset | Gamleboligsameie: Furusetveien 65, 1051 Oslo, Norge, visit suffix |
| Work Order state/status | 0 / 5, Scheduled | 0 / 5, Scheduled |
| Schedule state/status | 0 / 1, Planned | 0 / 0, New |
| Schedule name | SCH-test-ordre med asset | null |
| Resource | Magnus Hognas, dc0a2f69-3751-4749-8e5b-f315ca07c063 | Bram de Vries, 48eb06ab-9256-42f1-81e4-ff93f95bb46e |
| Schedule start/end UTC | Sep 22, 10:00-11:00 | Sep 24, 12:00-12:45 |
| Parent preferred window UTC | Sep 22, 10:00-12:00 | null / null |
| Schedule scheduledon and window fields | null | null |
| Owner | Magnus | Integration user |

The portal's naive 14:00-14:45 becomes 12:00-12:45 UTC correctly for Oslo in September. Customer, asset, Work Order and resource links are populated. Five sampled local assignments have remembered IDs but null cached status. AssignedVisitList already conditionally renders `resco_status`; only All Visits currently exposes the pull action.

Live `$metadata` confirms schedule status defaults to 0, name has a 160-character limit, schedule times are DateTimeOffset, and the existing resource/Work Order navigation bindings are valid. This establishes a payload gap, not proof of the planning screen's exact filter. No remote writes or status/reconciliation endpoint calls were made during proposal work.

## Goals / Non-Goals

**Goals:** Separate the status API from explicit reconciliation while retaining on-demand semantics; correct schedule initialization with verified tenant values; repair selected portal-owned bookings without creating replacements.

**Non-Goals:** Import Magnus's orders, introduce polling, infer current status from successful push, change overdue rules, rewrite datetime storage, or copy all fields from a manual order.

## Decisions

### Explicit cached status and two independent actions

Render a labelled last-known status, `Not yet refreshed` when an ID exists without status, and `Not synced` without an ID, in summary and expanded details.

All Visits offers two admin-only buttons:
- **Sync from Resco** reads current statuses and stores them locally. It never unassigns visits, clears pins, writes remote statuses or runs pending Draft-reset retries. It needs no destructive-action confirmation. Show pulled/skipped/failed counts and per-item errors.
- **Unassign past Scheduled visits** requests confirmation explaining that past planned visits currently Active/Scheduled will be unassigned, including pinned visits, and their Work Orders reset to Draft. It performs its own fresh status reads, so a prior sync is not required and stale cached values cannot authorize unassignment. It retains durable reset retries, conditional remote writes and failure reporting. Show locally unassigned, skipped/failed reads and remote reset failures separately.

Manual Assignment offers the same status-only **Sync from Resco** button. Share status-sync UI behavior across both screens: busy state, duplicate-submission prevention, result summary and refresh callbacks. Keep the unassignment control on All Visits. Reload visits and assignments after either action so status-dependent filtering and explicit reconciliation are reflected; a sync may hide completed overdue cards under existing display rules but must retain their assignments.

Refactor backend status reading/storage into a reusable operation separate from reconciliation and reset retry execution. Make the existing `POST /assignments/sync-resco-status` route status-only and add an explicit admin-only `POST /assignments/reconcile-resco-scheduled` route. Deploy frontend and backend together and update API helpers/types in sync. Status-only responses can retain the existing summary shape with reconciliation counters zero for compatibility; present only relevant counts. Reconciliation reuses existing eligibility, durable reset transactions and concurrency protections. An old client calling the sync route becomes less destructive; no route named sync silently retains unassignment behavior.

"Never made it past Scheduled" is interpreted as the existing current-status-only rule: planned_start before today plus a fresh parent Work Order statecode 0/statuscode 5. No audit-history claim is made. Today/future visits and other statuses remain assigned; failures protect the assignment. A Work Order that previously progressed and returned to Scheduled remains eligible under that existing rule. UI labels and explanations say "currently Scheduled" rather than "never took place".

No automatic status pull occurs on page load, push completion or startup. Failed reads retain last-known values and report errors; they never authorize reconciliation. Pending Draft resets are retried only by the explicit unassign operation, including when no current assignment remains for the pending reset.

### Initialize the schedule separately from the Work Order

Create schedule children with a stable human-readable name bounded to 160 characters, `statecode=0` and `statuscode=1`. Keep the existing parent Scheduled initialization and Europe/Oslo serialization. Keep initial status fields out of routine update payloads to avoid overwriting technician progress. Retain the remembered parent ID if child creation fails.

Before finalizing payload changes, verify Resco planning with the same resource/date/view filters as the manual reference. Planned versus New is the leading explanation. Inspect preferred windows and ownership filters if the named Planned child still does not appear. Add further fields only after proving their necessity and recording their business meaning here; do not fabricate scheduledon, travel values, due dates or assign ownership merely to mirror the example. A manual reference also has null scheduledon and child window fields, which argues against assuming those are mandatory.

### Repair selected existing schedules explicitly

Add a manual operator command with explicit service-visit selection and dry-run default, separate from startup, migrations and status reconciliation. Resolve only remembered portal identities, validate child-parent and resource/time consistency, and freshly check parent Active/Scheduled and child Active/New. Skip missing, inconsistent or progressed records with a reason. Fill the verified missing planning fields and promote only an eligible child. Use conditional writes with ETags, rechecking the parent immediately before writing; surface conflicts instead of blindly retrying writes. Record that cross-record parent/child atomicity is unavailable and avoid writing the parent during child-only repairs. No automatic whole-table push.

### Live visibility is an acceptance criterion

Compare one clearly scoped portal booking with the reference in Resco's actual planning UI. A 200 response or Planned label alone does not prove the UI issue resolved. Record date range, resource/view filters and before/after evidence. Preserve the manual reference untouched. If browser access is unavailable, leave visual verification unchecked and report that limit.

## Risks / Trade-offs

- Tenant-specific filters may require more than child status/name -> verify the screen and document minimal additional fields before implementation is considered complete.
- Manual reference and portal example use different resources/dates -> control filters and permissions during visual comparison; do not attribute causality to the sample comparison alone.
- Old callers may expect sync to reconcile -> deploy both layers together and document that sync is now status-only; confirmation belongs only to the separate unassign action.
- Remote changes can race repairs -> ETag-protect child writes, freshly inspect both records, and report conflicts; cross-record atomicity remains a limitation.
- A second manual example, Work Order `9b8c6b0c-aec7-49d4-849a-ecfd5ecdc42a`, reports Completed with statecode 0/statuscode 10001, while its child is 1/6. Existing completion logic assumes parent statecode 1. Record this separate finding for follow-up; do not expand this visibility change into completion/reconciliation redesign. Display returned labels accurately.

## Migration Plan

No database migration is expected. Deploy status UI and corrected schedule creation after mocked checks. Preview selected existing assignments, then repair eligible records with an explicit apply option and retain a before/after record. Confirm planning visibility. Roll back application changes if needed; do not blindly revert remote statuses because work may have progressed. Preserve existing IDs and data throughout.

## Resolved planning visibility

The controlled live comparison below confirms that initializing a named Planned child is sufficient for the tested Manager Schedule Board. Preferred-window and ownership changes were unnecessary.

## Implementation verification

On 2026-09-24, read-only reinspection confirmed the reference schedule remains Active/Planned and portal visit 97888 remains Active/New with no name, the same resource and times recorded above. No local assignment references the manual Work Order. The status-only route and separate reconciliation route are implemented; 45 focused backend tests pass, covering status-only non-mutation, existing reconciliation and reset retries, schedule payloads, and conditional selected-booking repairs.


Authenticated headless Edge verification opened Manager > Schedule Board for Sep 21-25 with all resources. Magnus's manual booking was present; portal visit 97888 was absent and Bram showed 0 booked time. After preview and conditional repair of only schedule `07089859-ae9d-46e9-8ae3-f8d2e5e40a4c` (name + Active/Planned), the booking appeared and Bram showed 45 minutes. Parent windows remained null; owner, resource, parent/child IDs and 12:00-12:45 UTC stayed unchanged. Repeating preview skips the now-Planned child. Magnus's reference retains modifiedon 2026-09-22T07:05:20Z. No further payload fields are needed for this tested view. Evidence screenshots are retained in the local temporary directory as fms-resco-board-before.png and fms-resco-board-after.png.

Portal browser checks used controlled API responses in headless Edge: both sync buttons, no POST on mount, unknown/unsynced/known statuses, expanded complete IDs, retained assignment after sync, partial failure, request failure, disabled busy state, cancelled unassignment without a request, explicit reconciliation and refreshed lists all passed without page errors. Frontend build passes; oxlint has the same six existing warnings and no new warnings.


Day-view hover confirmed repaired visit 97888 at 24 September 14:00-14:45 Oslo, Planned, on Bram's row (fms-resco-day-after.png). A new assignment exercised the updated sync path inside a rolled-back local verification transaction: visit 98318 produced Work Order `974a6970-cb05-4a1b-87ae-1a4823e578b7` and schedule `788a88c4-4c2d-4dae-9708-113f7dc26319`. Both are clearly named Manual Verify planning visibility; those two remote records remain, while the temporary local visit and assignment were rolled back. The Resco board showed this new Planned booking on Bram's row at 25 September 08:00-08:30 Oslo (fms-resco-new-booking.png).

Final checks: 79 backend tests pass, including authorization and endpoint dispatch; frontend build passes; six pre-existing lint warnings remain. Browser checks pass. No schema migration or TypeScript response-shape change was necessary: both endpoints retain RescoStatusSyncSummary, with reconciliation counters zero for status-only sync.

Operator repair usage from backend: `.venv/Scripts/python.exe -m scripts.repair_resco_schedules 97888` previews selected visit IDs; append `--apply` to write eligible repairs. Only visit 97888 was repaired during this change; other existing portal bookings require explicit selection. Deploy frontend and backend together because the existing sync endpoint now only reads statuses and the separate reconciliation endpoint owns unassignment and Draft-reset retries.
