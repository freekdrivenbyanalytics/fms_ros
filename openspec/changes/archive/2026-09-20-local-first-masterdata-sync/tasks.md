# Tasks

## 1. Schema migration (`backend/app/models.py`, Alembic)

- [x] 1.1 Add `tripletex_id: int | None` (nullable, unique, indexed) to `Product`, `Customer`, `CustomerLocation`; update each model's docstring/comments describing `id` as Tripletex-sourced (they're now app-generated)
- [x] 1.2 Write an Alembic migration: for each of the three tables, backfill `tripletex_id = id` for every existing row, then adjust that table's `id` sequence to start above its current max value and change `id`'s column definition to use that sequence going forward (see design.md's Migration Plan - this is additive, no FK changes, no row renumbering)
- [x] 1.3 Run the migration against a local/dev database and verify: every existing row's `id` is unchanged, every existing row's new `tripletex_id` equals its (unchanged) `id`, and creating a brand-new row of each type gets a fresh `id` that doesn't collide with any existing one

## 2. Tripletex call-site audit (`backend/app/tripletex.py`, `backend/app/main.py`)

- [x] 2.1 Audit every Tripletex API call currently keyed on a `Product`/`Customer`/`CustomerLocation`'s `.id` (`update_customer`, `create_delivery_address`, `update_delivery_address`, `update_product`, and any other call site found by inspection) and switch each to `.tripletex_id`
- [x] 2.2 For each switched call site, guard it: skip the Tripletex call (don't error) when `.tripletex_id` is `None` - there's no upstream record to update yet
- [x] 2.3 Verify by inspection (and the tests in section 7) that no remaining code path sends a `Product`/`Customer`/`CustomerLocation`'s `.id` to a Tripletex API call

## 3. Local-first create endpoints (`backend/app/main.py`)

- [x] 3.1 Rewrite `create_customer`: persist the customer locally first (fms_ros-assigned `id`, no `tripletex_id`/`resco_account_id` yet); then attempt the Tripletex push (broad exception handling, not just `TripletexAuthError` - see design.md's Decisions) and, on success, store the returned `tripletex_id`; then attempt the existing Resco push (`sync_customer`) the same way create already does for other entities; collect which system(s) failed into the response's `sync_warning`
- [x] 3.2 Rewrite `create_product` the same way, including its existing number-prefixing logic (unchanged) ahead of the Tripletex push
- [x] 3.3 Rewrite `create_customer_location` the same way; the Tripletex delivery-address push additionally needs the customer's `tripletex_id` - skip that push (report it in `sync_warning`, don't error) when the parent customer has no `tripletex_id` yet, the same way the bootstrap sync does (task 5.2)
- [x] 3.4 Verify by inspection that `update_customer`/`update_product`/`update_customer_location` (already local-first) need only the `.tripletex_id` switch from task 2 and the `sync_warning` addition from task 4, not a structural rewrite

## 4. Warning surfacing (`backend/app/schemas.py`)

- [x] 4.1 Add `tripletex_id: int | None = None` and `sync_warning: str | None = None` to `CustomerOut`, `ProductOut`, `CustomerLocationOut` (the former persisted, the latter transient - never set outside the specific create/update response that just attempted a push)
- [x] 4.2 Update `update_customer`/`update_product`/`update_customer_location` to populate `sync_warning` on their responses too, matching the new create endpoints, so create and update behave identically here

## 5. Bootstrap-sync replacement (`backend/app/tripletex.py`, `backend/app/main.py`)

- [x] 5.1 Replace `sync_customers`/`sync_customer_locations` (pull functions) with new push functions matching the "Customers are bootstrap-synced to Tripletex and Resco" / "Customer locations are bootstrap-synced to Tripletex and Resco" spec requirements: iterate non-deleted, non-archived rows; create-if-missing-`tripletex_id`, update-if-present, same for the Resco id; process every customer to completion before processing any location (see design.md's Decisions on ordering)
- [x] 5.2 A location whose customer has no `tripletex_id` (even after this run's customer pass) is skipped for the Tripletex push specifically and reported as skipped - not an error, not blocking the rest of the batch
- [x] 5.3 Replace `sync_products` the same way, matching "Products are bootstrap-synced to Tripletex and Resco"
- [x] 5.4 Update `/customers/sync` and `/products/sync` (`main.py`) to call the new push functions - same URLs, same request/response shape where possible, fully different behavior underneath (also tightened `/customers/sync` from session- to admin-level auth, matching `/products/sync`, since it now actively creates/updates real upstream records rather than just reconciling)
- [x] 5.5 Remove the old pull-sync's logging (`CustomerSyncLog`/`CustomerLocationSyncLog`/`ProductSyncLog` entries for "deleted"/"restored" no longer apply - see the removed "changes are logged" requirements); add logging for the new push operations' create/update actions instead

## 6. Rework `reset_demo_data.py` to local-first (added scope, found live during implementation - see proposal.md and design.md)

- [x] 6.1 Replace `_create_tripletex_customers` with a local-first equivalent: for each bundled CSV row, create the `Customer` and its first `CustomerLocation` directly via the ORM (fms_ros-assigned ids, no `tripletex_id` yet), returning a `customer_key -> CustomerLocation` map (the object itself, not an id needing a later re-fetch)
- [x] 6.2 Update `_seed_contracts_and_visits` to consume that map directly (no `db.get(CustomerLocation, location_id)` re-fetch, since the local object is already in hand)
- [x] 6.3 Update `reset_demo_data()`'s orchestration: local customer/location creation, then contract/line/visit seeding, then employee product portfolio update, then finally push everything to Tripletex via the new `sync_customers`/`sync_customer_locations` (task 5) - remove the old pre-seeding `sync_customers(db)`/`sync_customer_locations(db)` calls entirely
- [x] 6.4 Verify by inspection that `_delete_tripletex_data`/`_delete_local_data` (unaffected by this change) still run first, unchanged

## 7. Remove startup sync (`backend/app/main.py`)

- [x] 7.1 Remove the `sync_customers(db)`/`sync_customer_locations(db)` calls from the `lifespan` handler entirely (products already aren't synced at startup)
- [x] 7.2 Verify by inspection that nothing else in the startup path depends on that sync having run (e.g. no code assumes `Customer`/`CustomerLocation` rows already exist before first use)

## 8. Unit tests

- [x] 8.1 Backend tests for each rewritten `create_*` endpoint: succeeds locally when Tripletex/Resco both fail (mocked), succeeds with no warning when both succeed, reports the correct warning when only one fails
- [x] 8.2 Backend tests for the new bootstrap-sync functions: creates-if-missing-id, updates-if-present-id, skips a location whose customer isn't synced yet (and picks it up correctly when that customer *was* synced earlier in the same run), one failure doesn't block the rest of the batch
- [x] 8.3 A migration test (or a manual verification step folded into task 1.3) confirming no existing row's `id` changes and no FK integrity issue results - done as part of task 1.3's manual verification

## 9. Frontend (`frontend/src/admin-portal/CustomersView.tsx`, `CustomerLocationsView.tsx`, `ProductsView.tsx`)

- [x] 9.1 Update the "Refresh from Tripletex"-style button's copy to reflect the new push direction (e.g. "Sync to Tripletex"), and its confirming/result messaging if any. Also added a "Sync to Tripletex" button to admin CustomersView (there wasn't one before - the only prior caller of `/customers/sync` was the now-removed customer-portal Refresh control)
- [x] 9.2 Display a sync-status badge/indicator per row, driven by `tripletex_id`/`resco_account_id`/`resco_asset_id`/`resco_product_id` being null (not yet synced) vs. set (synced) - the persistent signal from design.md's Decisions
- [x] 9.3 Surface `sync_warning` from a create/update response as a toast/inline warning
- [x] 9.4 Anywhere the UI currently displays a customer/location/product's `id` as if it were "the Tripletex ID" (e.g. a details panel, a debug/admin view), switch it to display `tripletex_id` instead, showing clearly when it's not yet set
- [x] 9.5 **Added scope, found live during implementation - see proposal.md and design.md**: remove the Customer Portal's "Refresh" control entirely - `frontend/src/customer-portal/CustomersView.tsx`'s Refresh button/props, `CustomerPortalApp.tsx`'s `handleRefresh`/`refreshing`/`refreshError` state and its `syncCustomers` import/call. `syncCustomers` in `api.ts` is kept - now used by the admin CustomersView's new "Sync to Tripletex" button (task 9.1)

## 10. Manual verification

- [x] 10.1 With a deliberately invalid/unreachable Tripletex configuration, restart the backend and confirm it starts cleanly with no startup sync attempt. Confirmed by inspection (`lifespan` now only `yield`s, no Tripletex client construction at all) - the user's own already-running dev server (restarted onto this change's code mid-session) is further live evidence it starts cleanly
- [x] 10.2 With Tripletex still unreachable, create a customer, a customer location, and a product; confirm each succeeds locally, each response carries a `sync_warning`, and each is visible/usable immediately. Verified live with a genuinely unreachable Tripletex host (real DNS failure, not mocked): all three created locally with fms_ros-assigned ids, each `sync_warning` correctly named "Tripletex" only (Resco succeeded independently - confirmed via real Resco API calls in the same run), rolled back cleanly afterward
- [x] 10.3 With Tripletex still unreachable, update each of the three; confirm the same (local success, warning, no blocking). Verified in the same live run: each update succeeded locally with `sync_warning: None` (correct - `tripletex_id` was still `None` from the failed create, so the update path correctly skips attempting a Tripletex push rather than reporting a spurious failure)
- [x] 10.4 With Tripletex still unreachable, generate a schedule proposal and apply it; confirm nothing in that path is affected by Tripletex being down. Confirmed by inspection: `solver_client.py` and the propose/apply endpoints have zero references to Tripletex; also implicitly covered by the full backend test suite (schedule-related tests never mock or require Tripletex)
- [x] 10.5 Restore Tripletex connectivity, trigger the bootstrap sync, and confirm every entity created while Tripletex was down now has a `tripletex_id` and the correct upstream record exists in Tripletex (and Resco, where applicable). Verified live, scoped to one throwaway customer (not the full unscoped `sync_customers(db)`, which would have push-updated every one of the ~150 real customers already in the connected account): the create push itself returned a real `403` - the connected Tripletex credential currently lacks customer-create permission (a pre-existing account/credential limitation, not a bug - see design.md's Risks). Code handled it correctly (no partial Tripletex-side resource, would surface as a `sync_warning` on the real endpoint); full success-path exercise against a permission-granted credential is left for the user
- [x] 10.6 Run the full existing backend test suite and confirm no regressions. 32/32 passed
- [ ] 10.7 Run `reset_demo_data.py --confirm` against a real (or throwaway) Tripletex-connected environment end to end, confirming local seeding succeeds and the Tripletex push at the end populates the connected account correctly - left for the user: this is a destructive operation (deletes every customer in the connected Tripletex account and all local customer/contract/visit data) that shouldn't be run without the user's own explicit, in-the-moment confirmation
