# Design

## Context

See proposal.md for motivation. Repository inspection confirmed that Product has one optional service_order_type_id and ContractLine has multiple required_products. ServiceOrderType currently has only identity, name and soft-delete state; there is no Task model. Product sync already sends name/productnumber and remembers resco_product_id. Assignment sync creates a Work Order and schedule, but sends no price-list/currency fields, jobs or product lines.

The implemented `fix-resco-planning-visibility` change supplies named Active/Planned schedule children and separate read-only status refresh versus explicit overdue reconciliation. Preserve that implementation and the older archived Resco/local-first designs; this proposal neither reimplements nor archives that change.

Read-only inspection of the sfm tenant's OData metadata and representative records on 2026-09-24 established:

| Concept | Resco entity / verified relation |
|---|---|
| Job template | `fs_incidenttemplate`: name, pricelevelid_pricelevel, transactioncurrencyid_transactioncurrency |
| Template task | `fs_incidenttemplatetask`: name, description, duration, fs_taskorder; incidenttemplateid_fs_incidenttemplate |
| Applied Work Order job | `fs_workorderincident`: incidenttemplateid_fs_incidenttemplate and workorderid_fs_workorder |
| Instantiated Work Order task | `fs_workordertask`: workorderincidentid_fs_workorderincident, workorderid_fs_workorder; estimatedduration, completionpercent |
| Work Order product line | `fs_workorderproduct`: productid_product, workorderid_fs_workorder, workorderincidentid_fs_workorderincident, uomid_uom, transactioncurrencyid_transactioncurrency; estimatedquantity and quantity are distinct |
| Price list | `pricelevel`: name, transactioncurrencyid_transactioncurrency, statecode/statuscode |
| Currency | `transactioncurrency`: ISO code, name, symbol, precision, exchange rate |

The Work Order has a collection of fs_workorderincident children, so multiple job templates are supported without inventing a scalar template field. A template task has a single parent lookup, so a shared portal task needs one remote instance per association. The separate `fs_incidenttemplateproduct` entity exists but is explicitly outside this mapping.

Initial inspection found only EUR/USD currencies and four EUR/USD lists. After the user's setup, a fresh read confirmed active NOK currency `11f2e89b-45b3-451d-aba3-67ea257d9a41` (ISO NOK, name NOK). Still no NOK price list was present. The tenant's base currency is USD; this integration must not change that or the configured exchange rate. These IDs are evidence, not hard-coded application constants.

Proposal inspection found no template-application action (only GenerateReport functions). Apply verification subsequently disproved automatic expansion through OData, and the user authorized explicit task creation; see decision 4 and verification evidence below.

## Goals / Non-Goals

**Goals:** Independent reusable task master data; faithful type/template/task mapping; exactly one job per selected type and one line per selected product; explicit API task creation; a valid NOK price list on portal Work Orders; reliable partial-failure recovery.

**Non-Goals:** Tasks on products, exporting the product/type association as template-product rows, currency creation or exchange-rate maintenance, price calculation/rate tables, altering solver duration, importing manual Resco records, or rewriting progressed Work Orders from mutable template data.

## Decisions

### 1. Reusable tasks with an explicit association entity

User confirmed task reuse across types. Add Task (id, name, nullable description, nullable estimated_duration_minutes, delete_flag) and ServiceOrderTypeTask (type_id, task_id, position, delete_flag, remembered remote task ID and sync state). Use a unique type/task pair so removing and re-adding a link can reuse its remote identity. Keep per-type ordering on the association, not on Task. Add nullable resco_job_template_id and sync state to ServiceOrderType. Task is catalog data, not a scheduled visit or task completion record.

Use task name as the remote task name, description as description and estimated duration only when supplied. Stable positions determine fs_taskorder. Do not derive tasks from product names/numbers or assign contract-line visit duration to every template task. Null duration remains unspecified; the visit's scheduled duration remains unchanged.

A single resco_task_id on Task was rejected because Resco template tasks have one parent. Remote IDs belong to ServiceOrderTypeTask. Keep inactive associations and pending retirements so failed unlink operations remain retryable after local deletion. Soft-deleting a shared task marks all its active associations for retirement; soft-deleting a type stops new selection and retires its managed template for future use. Never hard-delete Resco records.

### 2. Local APIs and administration

Add admin-only task CRUD/list routes with the existing soft-delete conventions. Extend service-order-type in/out contracts with an ordered task_ids input and nested task summaries, remembered template ID and sync_warning output. Reject duplicate/deleted/missing task IDs. Expose type usage on task detail. Keep frontend types in sync with the new schemas.

Add Tasks to the Admin Portal navigation using the existing list/detail pattern. Service Order Types gets a task picker and simple move-up/down ordering controls, separate from its existing products display, plus Resco identity/warnings. Add an admin `POST /service-order-types/sync-resco` bootstrap/retry action with per-item results. Task edits sync each affected active type after the local transaction; type edits sync that type. Unlinked catalog tasks do not create standalone Resco records. No network call happens at startup or just by opening a view.

Add a `Sync to Resco` button on the Admin Portal Products page, backed by an admin-only `POST /products/sync-resco` endpoint using the existing `sync_products_to_resco` helper. Process all active products (exclude both archived and delete_flag), show created/updated/skipped/failed counts and item errors, disable the button while running, and refresh displayed data after completion. Keep the existing Tripletex action separate. Opening the page does not sync.

Reuse the existing `sync_product` create/update logic for both manual and post-commit automatic sync on product creation/editing: `resco_product_id` identifies the remote record to update with current mapped fields (name and product number); an absent remote ID means create and persist the returned ID. Local IDs, Tripletex IDs and names are not remote identity keys. Preserve the remembered ID on failure; do not fall back to creating duplicates when an update fails. Existing create/edit routes already call this helper, but must surface its returned failure result as a response warning, not rely only on exceptions. Verify successful repeated sync updates the same record. Product/type edits affect template selection for future assignments, not the task catalog or template task membership; do not export the product/type link.

### 3. Durable identity and retry sequencing

Extend the existing commit-local-first pattern. Sync currency/price-list prerequisites, then the template, then each active task association and pending retirement. Persist each successful identity before proceeding. Use durable type/task sync state so a failure can be retried from the admin action. Retire by the verified inactive state/status for the tenant; exact codes and whether inactive tasks are excluded from template application must be verified before completing the lifecycle implementation.

Allocate stable operation identities before remote creates and serialize sync per type/setup with database locks, not process-local locks. Verify whether Resco accepts caller-assigned record IDs for these entities. If supported, persist generated IDs before create and recover ambiguous timeouts by reading that exact ID. Otherwise use supported remote correlation/reconciliation to recover the same record; never use a display name as the sole identity or blindly repeat a timed-out POST. Prove retry/concurrent behavior before wiring automatic triggers.

### 4. Create named jobs and Work Order tasks explicitly

User authorized explicit API task creation after the live probe showed that linking a template through OData does not expand its tasks. Resolve distinct active service order types through the visit's selected products. Sync each type as a job template with its linked tasks, then create one fs_workorderincident per type with the template binding, Work Order binding and template/type name. Explicitly create fs_workordertask children from that type's full active ordered task list, including name, description, optional estimatedduration and fs_taskorder, linked to both the job and Work Order. A shared catalog task occurs once per applied job.

Persist the intended job name and task payload snapshot before remote creation. Allocate caller-supplied UUIDs and serialize work per Work Order using database advisory locks; record and reuse each remote identity across retries. Existing records are read by ID before retrying ambiguous creates. Once created, task contents and completion are never patched by scheduling or template changes. Retired task links are omitted from future snapshots. Tracking survives Assignment removal and does not reference mutable visit rows through foreign keys.

### 5. Product lines are a separate part of assignment sync

Ensure each selected active required product has its Resco Product, then create one fs_workorderproduct per Work Order/product pair, remembering its remote line identity. Bind product and Work Order; bind the matching applied job for a typed product. Untyped products still become lines without a fabricated template. A type's other catalog products are not added.

The portal currently has no per-visit quantity or pricing model. Proposed initial mapping is one planned unit (`estimatedquantity=1`) per distinct required product, `isservice` from TJN versus PRD, and the resolved NOK currency. Do not mark a product consumed or set actual quantities, price overrides, costs, taxes or discounts from guesses. Reuse an existing valid product unit if Resco requires one. Verify the minimal creation payload and automatic price behavior during the implementation probe; a missing required unit/price prerequisite must be reported rather than fabricated. Price-list entries and product unit administration are not invented as part of this task; if the tenant requires additional configuration, record the specific prerequisite before continuing that path.

Retain successful lines on partial failure. Repeated scheduling or master-data sync must not overwrite technician usage, actual quantity or remote pricing. Add line/application tracking independent of Assignment's lifetime, keyed by remote Work Order identity; do not infer membership from names.

### 6. Reuse configured NOK and ensure a price list

Resolve the active transactioncurrency by ISO NOK. Reuse the user-configured record and rate. Choose a validated configured Resco price-list ID when provided, otherwise reuse a single suitable active NOK list. If none exists, create an active list named NOK and remember its identity in durable integration settings. If several suitable lists exist, report ambiguity and request explicit configuration instead of selecting arbitrarily. Verify activation codes and currency binding live; the inspected existing lists use statecode 0/statuscode 100001.

Serialize setup resolution/creation across workers and persist its identity for retries. On use, validate that the remembered list is active and uses NOK. A name of NOK is insufficient if its currency is EUR/USD. Do not alter existing currency setup, exchange rates or the organization's base currency.

Set pricelevelid_pricelevel and transactioncurrencyid_transactioncurrency on new templates and Work Orders, before applying jobs/products. Existing ordinary reschedules must preserve nonempty commercial values. For portal records with missing pricing data, use the explicit catch-up path below. Price-list creation creates the catalog container, not invented product prices.

### 7. Selected existing Work Order catch-up

Provide a dry-run-by-default operator command selecting service-visit IDs with remembered portal Work Order/schedule IDs. Preview missing NOK fields, templates/jobs and product lines. Apply only to freshly checked Active/Scheduled work with no child progress and no conflicting non-NOK pricing. Use conditional writes and repeat checks at relevant boundaries; skip incompatible or progressed records with specific reasons. Preserve both IDs, resource and booking times. Only missing additions are eligible; do not rewrite a previously applied template snapshot. An existing matching job must be adopted/verified rather than reapplied.

This is separate from read-only status sync and overdue reconciliation. No startup bulk push, edits to Magnus's manual examples or automatic whole-table catch-up. Retry partially completed catch-up through its persisted application/line state.

## Risks / Trade-offs

- Explicit task creation can partially fail -> persist snapshots and stable IDs, read before retry, and preserve any existing task progress.
- Shared task changes affect multiple templates -> per-association identity/state, independent error reporting and retry; historical work stays a snapshot.
- Remote retirement may not remove a task from future applications -> verify with a newly applied job after unlink; do not mark lifecycle complete solely on PATCH success.
- Missing unit/pricing prerequisites can prevent product-line creation -> inspect actual tenant validation without inventing commercial values, and report actionable failures while preserving local assignments.
- Concurrent creates/ambiguous responses could duplicate templates, jobs or lines -> durable correlation plus database serialization and read-after-timeout recovery.
- More network operations extend inline assignment latency -> cache prerequisites within a batch and sync each distinct template once per run; retain per-assignment outcomes.

## Migration Plan

Use the next additive migration after the actual head at implementation time (currently 0027): task catalog/associations, remembered template identity and durable sync/application/product-line/setup tracking. Audit all local cleanup paths, including contract visit regeneration and demo reset, so tracking foreign keys do not break existing deletes. Keep remote ownership records where needed after Assignment removal.

Deploy backend and frontend together. Include a one-time initial-data backfill after the task schema is available: link `generell inspeksjon` to the existing `Generelle vaktmestertjenester` type, and link that same reusable task followed by `lett snømåking` to the existing `Vaktmestertjenester (vinter)` type. Use the existing spelling of the winter type (the request's `Vatkmestertjenester` is a typo), resolve existing types by their exact names rather than hard-coded tenant IDs, and report missing or ambiguous matches instead of creating replacement types. Leave task descriptions and estimated durations unset. Make the backfill transactional and repeat-safe without duplicating tasks/links, removing unrelated associations or resetting later administrator edits; it must not run on startup or trigger remote writes. Other types remain unchanged, and no tasks are generated from products.

Manage subsequent tasks and links through the new UI, bootstrap templates explicitly (including these initial task associations), and catch up selected eligible Work Orders after preview. NOK currency is already configured; create only the missing price list if still absent. Roll back application behavior by disabling the new hooks while preserving additive data and remote identities; never roll back by deleting progressed Resco records.

## Implementation Verification Gates

Before normal writes are enabled, prove explicit task creation, inactive-task exclusion, minimal product-line requirements and retry identity behavior on a clearly named minimal live example. These are tenant/API mechanics, not permission to change the requested behavior. Use mocks for ordinary tests and minimal remote fixtures for the live checks; record all remote IDs that cannot be cleaned up.


## Apply verification: 2026-09-24

Task 1.1 completed against the connected tenant. Metadata confirms the bindings in the context table. Successful live payloads used:
- Price list: name `NOK`, statecode 0/statuscode 100001, `transactioncurrencyid_transactioncurrency@odata.bind` to the existing active NOK currency. No currency or exchange-rate writes were made.
- Template: name plus `pricelevelid_pricelevel@odata.bind` and `transactioncurrencyid_transactioncurrency@odata.bind`; active defaults 0/1.
- Template tasks: name, duration 5, fs_taskorder 1/2 and `incidenttemplateid_fs_incidenttemplate@odata.bind`; active defaults 0/1. PATCH statecode 1/statuscode 2 on the second verification task succeeded, but exclusion from automatic application remains unverified.
- Work Order: verification name and the NOK price-list/currency bindings, left in default Draft state without a schedule.
- Applied job: name, `incidenttemplateid_fs_incidenttemplate@odata.bind` and `workorderid_fs_workorder@odata.bind`; active defaults 0/1.
- Product line: `productid_product`, `workorderid_fs_workorder`, `workorderincidentid_fs_workorderincident` and `transactioncurrencyid_transactioncurrency` bindings, estimatedquantity 1 and isservice true. Creation succeeded without an explicit unit or fabricated price; form-level usability is not yet verified.
All creates accepted and preserved caller-assigned UUID `id` values. Successful create/read is evidence for identity recovery, not yet proof of concurrency or timeout handling.

**Blocking finding for task 1.2:** creating the linked job via OData produced zero Work Order tasks despite two active template tasks. Subsequent reads, including several minutes later, still returned zero. No Work Order tasks were posted by the portal. Metadata advertises only GenerateReport functions and no template-application action.

Investigation of [Resco's work-order-generation documentation](https://docs.resco.net/wiki/Work_order_generation_in_resco.FieldService) found `FieldService.CreateWorkOrder`, a server plugin function accepting a single jobtemplateid and copying template children into a newly created Work Order. A read-only plugin export confirms FieldServicePlugin is installed. This does not yet establish a callable, retry-safe flow that applies multiple templates to the same existing Work Order, as required for both creation and catch-up. It would be incorrect to conclude that all Resco automation is unavailable; only the planned direct OData side effect has been disproven.

At the initial verification gate implementation paused because explicit task creation contradicted the then-current instruction. The user subsequently authorized explicit API creation, resolving this blocker; implementation and verification are recorded below.

Retained remote records (no remote deletion performed; NOK price list is intended setup, other records are clearly named Manual Verify fixtures):
- price: `d914889c-2bff-4b95-ac28-22555cbf47b1`
- template: `73538e9c-468a-4932-bfcb-e6e12473ca4c`
- tasks: `['3b099b94-cc5d-4a5f-a7ec-658734213f02', '12b37518-818f-4f0e-9ba6-748321f4d312']`
- workorder: `18cf0425-1666-420e-8140-bec5abc070ab`
- job: `a00d19bc-9b0f-4623-a275-df178dbb4334`
- product_line: `196e9c4e-c6ba-4aae-8ee9-7920fe4f8e80`


User decision: explicitly create Work Order tasks via the API and set the applied job name from the service order type/job template. This supersedes the earlier automatic-expansion requirement and resolves the recorded pause.


## Implemented operation and verification

- Migration `0028` adds tasks, ordered type/task associations, template identity/error, assignment create tokens and durable `resco_sync_records`. The generic ownership table stores immutable Work Order manifests plus stable IDs/payloads for each job/task/line and mutable template records. It intentionally has no business-row foreign keys, so assignment removal, visit regeneration and demo cleanup retain ownership. Task associations cascade only on explicit hard removal of catalog rows; normal deletion is soft.
- A PostgreSQL advisory lock serializes this integration across workers and remains held on a dedicated connection across identity commits. This is deliberately one integration lock initially (rather than independent type/setup locks); it prevents lock-order races at the cost of serialized sync throughput. Concurrent create and lost-response recovery tests prove stable identity reuse. Normal rescheduling leaves completed manifests/tasks/products unchanged.
- Work Order tasks are explicitly posted with both Work Order and applied-job bindings, name, description, optional estimatedduration and fs_taskorder. Applied job names equal their type/template names. Existing tasks are never patched by assignment sync. Conflicting/progressed catch-up is skipped; unambiguous existing jobs/tasks/lines are adopted, while ambiguous or incompatible task contents are reported for review.
- Task/type soft-delete endpoints return the deleted entity with sync_warning so remote retirement failures remain visible. Type `sync_error` persists until a successful retry. Products retain existing ID-based name/number sync and now have the admin bulk button/endpoint; returned automatic-sync failures also appear as warnings.

Rollout (from backend):

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m scripts.seed_service_order_tasks
.venv/Scripts/python.exe -m scripts.catch_up_resco_jobs 97489
.venv/Scripts/python.exe -m scripts.catch_up_resco_jobs 97489 --apply
```

Use the Admin Portal Service Order Types `Sync to Resco` action for explicit template bootstrap/retry and Products `Sync to Resco` for product bootstrap/retry. These are independent of Tripletex. Nothing pushes on startup or page load. Configure `RESCO_NOK_PRICE_LIST_ID` only to choose among multiple active NOK lists; currency/rates remain managed in Resco. The one-time local seed marker prevents later runs from resetting administrator edits.

Live results:
- Local task seed ran successfully. General type 1 and winter type 2 share task 11 (inspection), and winter additionally has task 12 (snow clearing); no descriptions/durations were invented. Repeated seed is a no-op.
- Actual templates: general `f6d4be4e-21e0-48d3-82f6-9a201fec127a`; winter `22cda0c7-6f90-48db-92f7-26f7458259df`. Both synced with their tasks and without template-product links.
- Existing verification fixture received explicit task IDs `bd53c4ef-b9d5-5094-8212-8653cdc0cdeb` and `8e2cfa49-03c7-573b-b465-45b5dd6c54f6`; repeat reads recovered exactly those IDs.
- Multi-type fixture `Manual Verify Portal Jobs and Tasks 2026-09-24`: Work Order `e7881c8c-6e29-4691-bcb6-e9ea8897acb6`, schedule `9ad304f5-29b7-4296-b5d8-0e1c50453378`. Contains exactly two correctly named jobs, three tasks (inspection once under each job plus snow clearing under winter), and the two selected product lines. Repeated population creates no duplicates. Full child IDs are in local `backend/.local/resco-jobs-live.json`.
- Browser opened this Work Order in Resco, showing both job template names, all three ordered tasks and both products with no empty-price-list error. Currency/price fields are hidden by the tenant's loaded form rules; API reads verify NOK and the configured NOK price-list IDs. Screenshot: local `backend/.local/resco-workorder-nok-verified.png`.
- Selected portal visit 97489 previewed and caught up successfully: Work Order `21f4429e-9bd6-40b0-b2ca-290245e33f30`, schedule `16418b06-e7f1-4d75-827b-b10c2e3ee16e`. Repeat preview reports already populated. Fresh reads confirm planned start/end and resource still match the local assignment, and the Work Order now references NOK and price list `d914889c-2bff-4b95-ac28-22555cbf47b1`.
- Browser verification with controlled API responses covered task create/edit/delete, shared task selection/reordering, local-save warnings, template retry, Products sync results and separate Tripletex control. Only the explicitly clicked sync actions issued sync requests. Local screenshot: `backend/.local/products-resco-verified.png`.

Retained verification records are intentional and clearly named; no Resco records were deleted. The NOK list and actual templates/tasks are production setup, not throwaway fixtures.

Final checks: `pytest tests/ -q` passed 107 tests, including cross-session serialization, lost-create-response recovery, full assignment retry, task lifecycle, product sync, authorization and catch-up. `npm run build` passed. `npx oxlint` exited successfully with the same six pre-existing warnings. Strict change validation and all 22 main specs passed.

Post-restart verification (2026-09-25): backend :8000, frontend :5173 and solver :8100 responded successfully. The running backend exposes the new task and sync endpoints and uses migration 0028. Authenticated reads returned the two seeded tasks and two service order types. A browser check against the actual running backend (no mocked responses) verified the Tasks view, winter type task associations, template sync action, and separate Products Resco/Tripletex controls. No browser errors or mutation requests occurred. Local screenshot: `backend/.local/restarted-admin-verified.png`.

## User follow-up: 2026-09-25

Read-only inspection found that general template f6d4be4e-21e0-48d3-82f6-9a201fec127a was already active and synced. Visit 97272 Work Order 4b2eb440-5f88-42ef-87af-c92760d0fb54 already had job 9bda7bea-acee-4d7b-9b8c-1a3d36cfa92f, inspection task ac6badbc-df04-4d4c-bcd6-f66ec1546747 and direct product line 32c6ca79-721d-4e89-99c9-771adfc41d92 before follow-up writes. Parent creation was 05:36:27 UTC and final child creation 05:37:22 UTC: children are populated sequentially and are not atomically visible with the parent. This may explain an initially empty view; browser visibility must be checked separately.

98318 belongs to the prior planning-visibility fixture (Work Order 974a6970-cb05-4a1b-87ae-1a4823e578b7). That fixture's local assignment/visit were rolled back; it is not the jobs/tasks verification fixture and cannot safely be inferred as a current assignment for catch-up.

Confirmed omission: product-master payloads only sent name/number, leaving TJN10002 isservice false and currency/default price list null. The user explicitly extends this change to fix those defaults. Live metadata confirms writable product.isservice and transactioncurrencyid_transactioncurrency/pricelevelid_pricelevel bindings. Create/update now use the same validated NOK setup as Work Orders; assignment orchestration passes its already-resolved setup to avoid reacquiring the advisory lock. No unit, price, cost, rate or base-currency fields are sent.

Follow-up results:
- Corrected TJN10002 in place using the updated sync helper. Fresh remote read confirms product d0b1d505-21cc-43d0-9a90-992c364451a2 has isservice=true, NOK currency 11f2e89b-45b3-451d-aba3-67ea257d9a41 and NOK price list d914889c-2bff-4b95-ac28-22555cbf47b1.
- Retried normal assignment sync for 97272 successfully; fresh reads confirm the same job/task/product-line IDs with no duplicates.
- Authenticated browser check in Resco Manager opened Work Order 00148 (visit 97272), its general job, and the linked general template. The template form shows `generell inspeksjon` and no template products, as intended. To reach it: WorkOrders -> visit 97272 -> WorkOrder Job Template -> general job -> Job Template link. The Manager navigation does not expose a standalone template list.
- WorkOrder Products shows a generic `Service` row. Opening that row displays Product `Vaktmesteravtale 1-23`, which API identity confirms is TJN10002. This is a direct Work Order product line, not a template product. The row's missing product label is a remaining tenant presentation limitation; no tenant form/view changes were made. A form amount input also renders a euro symbol despite verified NOK record bindings, so API currency correctness must not be represented as proof of all UI currency formatting.
- Browser evidence: backend/.local/resco-97272-verified.png and resco-97272-job-verified.png; detail checks captured actual template/task and product lookup contents. Direct deep links loaded without navigation did not render forms in this app; following the in-app links worked. A combined script later timed out clicking a covered parent row, then a separate fresh Work Order session successfully opened the product detail.
- Regression: 112 backend tests passed (including TJN/PRD create/update payloads and NOK prerequisite failure). Frontend build passed; oxlint has the same six existing warnings. Strict change validation and all 22 main specs passed. git diff --check reported no whitespace errors. Running backend uses --reload. No commit, push, archive or new remote verification fixture.

## Visit duration follow-up

User requested visit duration on the single selected product. Resco metadata exposes separate integer estimatedduration and duration fields on fs_workorderproduct. Use estimatedduration (minutes) from contract_line.duration_minutes, the same source used by manual assignment to calculate the visit end. Apply only when exactly one active selected product is TJN; a physical product has no service time, and allocating across multiple products requires a later rule. Snapshot the estimate before line creation; preserve it on retries and leave existing estimates/actual field usage unchanged on rescheduling. This is visit-specific line data, not shared Product or template-task data. Repair the explicitly discussed 97272 line only after fresh Scheduled/no-progress checks, using a conditional PATCH for the missing estimate.

Confirmed all product master creation/update/bulk paths use sync_product and the same payload: isservice is true exactly for TJN, and validated NOK currency/default price list are always sent. Existing regression tests exercise both create and update for TJN/PRD.

Live duration verification found that estimatedduration=45 appears in the product detail form, but the service list still rendered 00:01 from estimatedquantity=1. Updated the single-service mapping to send both estimatedduration and estimatedquantity as the visit minutes. This supersedes the original one-planned-unit mapping for single-service visits only; physical/multiple-product quantities retain the prior mapping. Resco's getting-started documentation describes products versus service minutes (https://docs.resco.net/wiki/Getting_started_with_resco.FieldService). No actual duration, quantity or price values are set. The targeted 97272 repair now sets both estimates to 45 after no-progress and identity checks using ETags.

Final duration verification: fresh authenticated browser session shows 00:45 in visit 97272's WorkOrder Products list. Product detail shows estimated duration 45. The original product line ID is unchanged; actual duration and quantity remain unset. Screenshot backend/.local/resco-97272-verified.png refreshed. All 116 backend tests pass, strict change validation passes, and 22 main specs pass. No frontend code changed in this follow-up.
