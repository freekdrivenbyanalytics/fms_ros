# Tasks

## 1. Verify Resco application mechanics

- [x] 1.1 Recheck tenant metadata and active NOK setup, then document the exact template/task/job/product-line/price-list payloads and activation codes in design.md; verify each binding against the live schema without changing existing currency or rates.
- [x] 1.2 On the existing clearly named live example, verify explicit API creation of two Work Order tasks linked to the job and Work Order, preserving template task name/description/duration/order; verify stable IDs support retry without duplicate jobs/tasks.
- [x] 1.3 Verify inactive template-task exclusion on a new application, minimal selected-product line requirements (planned quantity, unit and pricing), and stable create identity/ambiguous-response recovery; record the observed behavior and any concrete missing prerequisites in design.md before wiring normal writes.

## 2. Add portal task master data and associations

- [x] 2.1 Add additive migration(s) and models for reusable tasks, ordered soft-deletable type/task associations, template identity, durable sync state, Work Order job/product-line ownership and NOK price-list identity; verify upgrade preserves existing rows and cleanup/assignment-removal paths retain or remove tracking appropriately.
- [x] 2.2 Implement admin-only task CRUD/list and ordered service-order-type task editing, with matching schemas; verify authorization, nonblank names, optional positive durations, invalid/duplicate/deleted task links, sharing, ordering and soft deletion with backend tests.
- [x] 2.3 Preserve local writes and report downstream result failures through response warnings, including task edits affecting multiple types; verify partial remote failure leaves the task and associations persisted and retryable.
- [x] 2.4 Add the one-time initial-data backfill: `Generelle vaktmestertjenester` gets `generell inspeksjon`; `Vaktmestertjenester (vinter)` gets that same task followed by `lett snømåking`. Test shared identity, order, unset descriptions/durations, missing/ambiguous type handling, repeat safety, preservation of unrelated data and later edits, and absence of remote writes.

## 3. Sync templates, task links and NOK price lists

- [x] 3.1 Implement NOK currency lookup and validated price-list reuse/create with durable identity and concurrency control; test missing/inactive currency, wrong-currency lists, ambiguous selection, repeated/concurrent setup and unchanged exchange rates/base currency.
- [x] 3.2 Implement template creation/update and ordered template-task sync keyed by type/task association; verify shared tasks produce separate correctly linked remote records, renames/clears update in place, and no template-product links are sent.
- [x] 3.3 Implement task unlink/delete and type-delete retirement plus durable pending retries; verify future template applications exclude retired tasks while existing Work Order task contents/progress remain unchanged, including remove-and-readd identity reuse.
- [x] 3.4 Wire post-commit type/task sync hooks and an admin template bootstrap/retry endpoint; test that startup and read-only page/API loads do not sync, item failures do not stop the batch, and partial/ambiguous responses cannot create duplicate templates or task children.

## 4. Populate Work Order jobs and selected products

- [x] 4.1 Resolve distinct active types from assignment products and apply each current template using the explicit job/task API flow; test same-type deduplication, multiple types, untyped/deleted-type products, shared task behavior and preserved local assignment on failure.
- [x] 4.2 Ensure selected Resco Products and create one remembered Work Order product line per selected product, with the correct job when typed; test that unselected products from the same type are excluded, no tasks are derived from products, and actual usage/pricing values survive retries and rescheduling.
- [x] 4.3 Add NOK price list and currency to new Work Orders/templates and durable application snapshots/recovery; test failures between parent/schedule/job/product steps, fresh-read recovery after timeouts, and preservation of task progress, identities and existing Planned schedule behavior.
- [x] 4.4 Add selected-record catch-up with dry-run default, explicit apply and conflict/progress checks; verify only eligible portal-owned missing data is added, existing non-NOK pricing/manual records are untouched, and repeated catch-up does not duplicate generated tasks, jobs or product lines.

## 5. Add Admin Portal controls

- [x] 5.1 Add Tasks list/detail/create/edit/soft-delete UI and service-order-type usage display, keeping API helpers and TypeScript contracts aligned; verify browser CRUD and field validation with controlled responses.
- [x] 5.2 Add type task selection/reordering and template identity/warnings, plus explicit template sync results/retry; verify one task can be shared by two types, product associations remain separate, failures are visible and opening views sends no remote sync request.

- [x] 5.3 Add the Products page `Sync to Resco` button and admin-only `/products/sync-resco` endpoint reusing existing helpers; show busy state, counts, per-product failures and refreshed data. Verify automatic create/edit sync reports returned failures as warnings, updates by remembered Resco ID, creates and persists an ID when absent, excludes archived/deleted products from bulk sync, preserves local saves on failure, and never exports product/type links. Cover authorization, mixed-success batches, repeated sync identity and UI behavior.

## 6. Verify end-to-end behavior and document operation

- [x] 6.1 Run relevant backend tests, frontend npm run build and npx oxlint; record pass/fail results and distinguish pre-existing warnings from introduced ones.
- [x] 6.2 Verify a live new Work Order with two types, a shared task and selected products: both jobs exist, API-created tasks have correct parent links/order, only selected products appear, and the Work Order opens without the empty-price-list error using NOK; record fixture IDs and browser evidence.
- [x] 6.3 Preview and apply catch-up to a selected eligible portal Work Order and rerun the preview; verify IDs/times/resource and progress protections, capture results, and document the operator command and any retained remote verification records.
- [x] 6.4 Document setup/rollout and retry behavior, reconcile implementation findings with all artifacts, and run openspec validate sync-resco-job-templates-and-tasks --strict plus openspec validate --specs before archive.


Final verification: 107 backend tests passed; frontend build passed; oxlint exited successfully with six pre-existing warnings and no new warnings. Strict change validation and all 22 main specs passed. Migration 0028, one-time task seed, live template sync, explicit job/task/product creation, browser verification and selected catch-up are complete. No commit, push or archive performed.

## 7. Follow-up from live user verification (2026-09-25)

- [x] 7.1 Verify the actual general template, visit 97272 children and origin of fixture 98318; distinguish API evidence from browser visibility.
- [x] 7.2 Map product master isservice from TJN/PRD and set validated NOK currency/default price list for create/update; repair TJN10002 in place and test failure/retry behavior.
- [x] 7.3 Verify browser visibility of the general template and visit 97272 job/tasks/direct product line, repeat sync without duplicates, and record remaining limitations honestly.
- [x] 7.4 Run regression tests and OpenSpec validation and record results.

## 8. Visit duration on service product lines

- [x] 8.1 Confirm all product sync paths apply TJN-only service classification and NOK defaults.
- [x] 8.2 Add single-service visit duration to the durable product-line estimate; test physical/multiple-product exclusion and retry/progress preservation.
- [x] 8.3 Fill visit 97272's missing estimate safely, verify Resco display, and run regression/spec checks.
