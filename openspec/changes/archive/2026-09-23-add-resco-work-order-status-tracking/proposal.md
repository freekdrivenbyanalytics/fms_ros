# Proposal

## Why

Portal customers must map to Resco customers, and their service locations must map
to Resco functional locations with their own addresses and coordinates. Each functional
location needs a same-named Asset for Work Order linkage. Work Orders also lack a
required customer binding, remain Draft after creation, and do not return field status
to the portal. Technical remote IDs must be visible for tracing these links.

## What Changes

- Keep one Resco Account per portal Customer, named after the customer. Sync contact
  name, email, telephone, mobile and organization number, including updates and clears.
  Add missing editing fields and repeatable fictional demo contact seeds.
- Map each CustomerLocation to a functional location carrying its address/coordinates;
  create or update one Asset linked to that functional location and parent Account.
  Functional location and Asset share the portal location's display name (address).
- Persist actual Account IDs on Customers, and functional location/Asset IDs on locations.
  Show these IDs read-only beside Tripletex IDs in portal details; also show Work Order
  and schedule IDs on assigned-visit details, including partial sync results.
- Bind each Work Order to its visit location's Asset and the parent customer Account.
  Keep `Customer name: address | Visit <service_visit_id>` as its descriptive name,
  retaining the unique suffix within the name limit and reusing remote IDs on updates.
- Explicitly set new Work Orders Scheduled. Pull statuses on demand for previously
  synced assignments and display them on cards, Day Planning and All Visits.
- **BREAKING**: portal reconciliation unassigns only past planned assignments whose
  Work Orders are currently Scheduled. Never-synced visits, failed reads and other statuses
  are excluded. Eligible assignments may be unassigned despite pin/elapsed-time locks;
  record the reason and attempt to reset that Work Order to Draft. Report reset failures
  independently and retain retry context. Use fresh current status; audit history is not required.
- Preserve the board's completed-overdue hide rule (requested_date before today),
  while All Visits remains unfiltered and Day Planning keeps completed blocks visible.
- All Visits has no per-visit edit controls; its admin bulk status-sync/reconciliation
  action is an explicit exception to read-only presentation.
- Catch up missing functional locations, Asset links and portal-linked Work Orders
  without duplicating existing Accounts/Assets or resetting progressed work.

## Capabilities

### Modified Capabilities
- `resco-integration`: customer Accounts, functional locations, Asset/Work Order bindings and names,
  Scheduled creation, on-demand status pull, narrowly scoped Draft reset.
- `customers`: functional-location identity, contact editing, technical-ID visibility and sync.
- `assignments`: status, reconciliation eligibility, lock exception, reason and board visibility.
- `day-planning`: status display without hiding completed blocks.

### New Capabilities
- `visit-history`: unfiltered All Visits page with the admin bulk action.

## Impact

Backend Resco client/syncs, schemas, ORM models, additive migrations and relevant
customer/assignment routes; frontend types, API calls, cards, timelines and All Visits.
Tests must cover independent functional locations, retries and migration links, optional
coordinates, repeat-visit naming, protected statuses and failed pulls, Draft reset
failures and reassignment. Live verification must confirm functional-location coordinates in the
field-facing view and the Scheduled-to-Draft transition. No application code changes
are part of this specification revision.


## Related follow-up changes

Recommend separate `add-service-order-type-tasks` and then
`sync-resco-job-templates-and-skills` changes for the requested reusable task catalog,
service order type task sets, Skills sync, product-free job templates and assigned
Work Order template/product/task payloads. Their requested examples and unresolved
multi-product/template mapping are recorded in design.md. These are planned follow-up
scopes, not completed or separately scaffolded changes.
