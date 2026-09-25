# Proposal

## Why

The portal already pushes product names/numbers and scheduled Work Orders to Resco, but it has no task entity, job-template sync or Work Order job/task population. Work Orders also omit the price list that Resco's form requires, and live inspection found no NOK price list. The user has now configured NOK currency.

## What Changes
- Add a `Sync to Resco` button on the Admin Portal Products page to push all active products. Set product isservice from TJN/PRD and validated NOK currency/default price list on create/update. Preserve automatic sync after product creation/editing: update by stored Resco Product ID or create and remember the ID when absent, with visible failure warnings and retry results.
- Populate the existing service order types with initial tasks: `Generelle vaktmestertjenester` gets `generell inspeksjon`; `Vaktmestertjenester (vinter)` gets the same shared `generell inspeksjon` task followed by `lett snømåking`.

- Introduce portal Tasks with a name, optional description and optional estimated duration, plus ordered links from service order types. Tasks are independent of products; no tasks are generated from product names.
- Sync each service order type as a Resco job template, together with its active tasks and template/task connections. Keep product master-data sync intact and do not create Resco template-product links.
- Derive distinct service order types through a visit's required products and attach one corresponding job per type to its Work Order. Explicitly create Work Order tasks through the API from each service order type's active ordered task list; also sync the visit's selected products as Work Order product lines. Preserve existing Work Order/task progress on later syncs.
- Reuse the configured active NOK currency and resolve or create an active NOK price list, use them on new portal Work Orders and templates, and provide selected-record catch-up for existing portal Work Orders missing these additions.
- Add admin task management, service-order-type task selection/order, Resco sync feedback and an explicit template bootstrap/retry action. Keep local writes successful when Resco is unavailable.

## Capabilities

### New Capabilities

- `tasks`: Independent task master data, validation, list/create/update and soft deletion.

### Modified Capabilities

- `service-order-types`: Ordered task associations and remembered Resco template identity.
- `admin-portal`: Task management and service-order-type task editing/sync feedback.
- `resco-integration`: Template/task mapping, multi-template Work Orders with explicit API-created tasks and selected product lines, safe retries and NOK price-list setup.

## Impact

Additive database migration(s), backend models/schemas/routes and Resco orchestration, frontend Admin Portal/API/types, optional configuration for explicit NOK price-list selection, tests and a selected-record catch-up command. No solver or recurrence changes. Build on the implemented `fix-resco-planning-visibility` change, preserving named Planned schedules and separate status-sync/reconciliation actions.

Confirmed decisions: tasks are reusable across service order types; applying a type uses its full active task list; the portal explicitly creates Work Order tasks through the API and names each job after its template/type; products are separately synced onto the Work Order. The user configured NOK currency and its exchange rate; reuse this setup without currency/rate management. Product/type membership remains local and is used only to select templates.
