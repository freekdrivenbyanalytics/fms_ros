## 1. Live verification (before building on top of either mechanism)

- [x] 1.1 Verify live how to add a new delivery address to an *existing* Tripletex customer — confirmed: `PUT /customer/{id}` with a nested `{"deliveryAddress": {...}}` object creates a genuinely new, independent delivery address each call (verified by creating two on the same throwaway customer and confirming both existed independently), while `PUT /deliveryAddress/{id}` directly (already proven in the prior change) is for updating one in place. Throwaway customer and both its delivery addresses were deleted and confirmed gone.
- [x] 1.2 Verify live what fields Tripletex actually requires to create a product — confirmed: `number`/`name` alone succeeds (`201`), Tripletex fills in the rest with defaults. Bonus finding: `DELETE /product/{id}` actually works (`204`) — the throwaway test product (`ZZTEST001`) was created and then successfully deleted, confirmed gone from a subsequent list.

## 2. Data model

- [x] 2.1 Add `resco_product_id` (`String`, nullable) to `Product` in `backend/app/models.py`
- [x] 2.2 Add `archived` (`Boolean`, `NOT NULL`, default `false`) to `Customer`, `CustomerLocation`, and `Product` — a second, sync-independent soft-delete flag (see design.md's "Decisions"). `sync_customers`/`sync_customer_locations`/`sync_products` in `backend/app/tripletex.py` MUST NOT read or write this field, ever — only the new create/update/delete endpoints touch it.
- [x] 2.3 Update every existing list query for customers, customer locations, and products (`list_customers`, `list_customer_locations`, `list_products`, and any other query filtering on `delete_flag.is_(False)`) to also filter `archived.is_(False)` (also found and fixed in `geofencing.py`, `resco.py` (both Resco sync functions), `seed.py`, and `tomtom_routing.py`, beyond the ones named in this task)
- [x] 2.4 Add an Alembic migration adding `resco_product_id` and the three `archived` columns — purely additive, no backfill needed
- [x] 2.5 Add `product_type` (`String`, `NOT NULL`, `server_default='TJN'`) to `Product` in `backend/app/models.py` and a migration adding it (see design.md's "Product type field" decision — closes the gap where a locally-created product outside the synced number-prefix range would get wrongly marked deleted by the next Tripletex sync). Migration `0019_product_type.py` run successfully against the dev database.
- [x] 2.6 Widen `TripletexClient.get_products`'s number-prefix filter from the single `PRODUCT_NUMBER_PREFIX` ("TJN") to a `PRODUCT_NUMBER_PREFIXES` tuple including both `"TJN"` and `"PRD"`; update `_apply_product_fields` in `backend/app/tripletex.py` to always derive `product_type` from the product's actual `number` prefix, for both Tripletex-native and locally-created products

## 3. Tripletex client methods

- [x] 3.1 Add `create_delivery_address(customer_id, data) -> dict` (or whatever shape task 1.1 confirms) to `TripletexClient` in `backend/app/tripletex.py`
- [x] 3.2 Add `update_delivery_address(location_id, data) -> dict` to `TripletexClient` (a direct `PUT /deliveryAddress/{id}` — already proven to work during the prior change's incident cleanup, just not yet a formal client method)
- [x] 3.3 Add `create_product(data) -> dict` and `update_product(product_id, data) -> dict` to `TripletexClient`, using the payload shape confirmed in task 1.2

## 4. Resco client methods (Product only — Customer/CustomerLocation already push to Resco)

- [x] 4.1 Add `create_product`/`update_product` methods to `RescoClient` in `backend/app/resco.py`, sending `name`/`productnumber` to the `product` entity set
- [x] 4.2 Add `sync_product(db, product) -> ProductRescoSyncResult` and `sync_products_to_resco(db) -> RescoSyncSummary` in `resco.py`, mirroring `sync_customer`/`sync_customers_to_resco`

## 5. Backend schemas and endpoints — Customer

- [x] 5.1 Add `CustomerCreate` (`name: str`) and `CustomerUpdate` (all editable fields) schemas to `backend/app/schemas.py`
- [x] 5.2 Add `POST /customers` in `backend/app/main.py`: push to Tripletex via `create_customer`, persist locally using Tripletex's returned id, then attempt a Resco sync (best-effort, non-blocking, same pattern as employee/customer create) before returning. A Tripletex push failure fails the request (create the customer nowhere, not just locally).
- [x] 5.3 Add `PATCH /customers/{customer_id}` in `backend/app/main.py`: persist the change locally, push the same change to Tripletex via `update_customer` (best-effort — log and continue on failure, matching the existing update-triggers-sync pattern), then attempt a Resco sync
- [x] 5.4 Add `DELETE /customers/{customer_id}` (soft-delete: set `archived` — NOT `delete_flag`, see task 2.2 — no Tripletex/Resco call)

## 6. Backend schemas and endpoints — CustomerLocation

- [x] 6.1 Add `CustomerLocationCreate` (`customer_id: int`, address fields) and `CustomerLocationUpdate` (address fields) schemas
- [x] 6.2 Add `POST /customer-locations`: push to Tripletex via `create_delivery_address` (task 3.1), persist locally using Tripletex's returned id, then attempt a Resco sync. A Tripletex push failure fails the request. The `address` display field and initial geocode are built locally from the submitted address fields (not from Tripletex's response), since the nested-object creation response's exact field shape for `addressAsString`/`displayName` was never verified live and the spec requires the location be retrievable with the address the user provided regardless.
- [x] 6.3 Add `PATCH /customer-locations/{location_id}` (address fields, distinct from the existing coordinates-only PATCH): persist locally, push to Tripletex via `update_delivery_address` (best-effort), then attempt a Resco sync
- [x] 6.4 Add `DELETE /customer-locations/{location_id}` (soft-delete: set `archived` — no Tripletex call, since Tripletex has no delivery-address delete)

## 7. Backend schemas and endpoints — Product

- [x] 7.1 Add `ProductCreate` (`product_type: Literal["TJN", "PRD"]`, `number: str`, `name: str`) and `ProductUpdate` schemas (updated after task 2.5/2.6 introduced `product_type`)
- [x] 7.2 Add `POST /products`: prefix `number` with `product_type` (skip if already prefixed), push to Tripletex via `create_product`, persist locally using Tripletex's returned id, then attempt a Resco sync. A Tripletex push failure fails the request.
- [x] 7.3 Add `PATCH /products/{product_id}`: re-prefix the number per `product_type`, persist locally, push to Tripletex via `update_product` (best-effort), then attempt a Resco sync
- [x] 7.4 Add `DELETE /products/{product_id}` (soft-delete: set `archived`, no Tripletex call)
- [x] 7.5 Add `resco_product_id` to `ProductOut` in `backend/app/schemas.py`

## 8. Frontend

- [x] 8.1 Add `CustomerCreateInput`/`CustomerUpdateInput`, `CustomerLocationCreateInput`/`CustomerLocationUpdateInput`, `ProductCreateInput`/`ProductUpdateInput` types to `frontend/src/types.ts`; add `resco_product_id` to the `Product` type (also added `product_type`, and address-line/postal/city fields to `CustomerLocation`, needed by the edit form)
- [x] 8.2 Add `createCustomer`/`updateCustomer`/`deleteCustomer`, `createCustomerLocation`/`updateCustomerLocation`/`deleteCustomerLocation`, `createProduct`/`updateProduct`/`deleteProduct` client functions to `frontend/src/api.ts`
- [x] 8.3 Add a create/edit form and soft-delete control to `frontend/src/admin-portal/CustomersView.tsx` (name field; email/phone/org number editable too, following the existing detail-view fields), following the Employee Management form pattern
- [x] 8.4 Add a create/edit form (address fields) and soft-delete control to `frontend/src/admin-portal/CustomerLocationsView.tsx`, alongside the existing coordinates-override form; a location's create form must let the user pick which customer it belongs to. `AdminPortalApp.tsx` updated to pass `customers` into this view.
- [x] 8.5 Add a create/edit form (type, number, name) and soft-delete control to `frontend/src/admin-portal/ProductsView.tsx`, replacing its current fully-read-only list/detail

## 9. Manual verification

All verified live against the API directly (not through the Admin Portal UI, which is covered by the frontend build/type-check instead) on a throwaway dev server, using a `ZZ TEST` customer, its location, and a `PRD99999TEST` product — all three fully cleaned up afterward (Tripletex: delivery address blanked/customer deleted/product deleted; Resco: account/asset/product deleted; local DB: rows and their sync-log references removed).

- [x] 9.1 Ran the migration; confirmed an existing product (`TJN10001`) is unaffected and `resco_product_id` is null, with `product_type` backfilled to `"TJN"`
- [x] 9.2 Created a customer via `POST /customers`; server log shows `POST /v2/customer` (201) then `POST .../account` (201) — Tripletex id `122725128` adopted, `resco_account_id` populated in the response
- [x] 9.3 Created a customer location via `POST /customer-locations`; server log shows `PUT /v2/customer/122725128` (200, nested `deliveryAddress`) then `POST .../fs_asset` (201) — Tripletex id `462837512` adopted, `resco_asset_id` populated, `address` built as `"Testveien 1, 0001 Testby"`
- [x] 9.4 Updated the customer (`PATCH /customers/{id}`) and location (`PATCH /customer-locations/{id}`); server log shows `PUT /v2/customer/122725128` (200) and `PUT /v2/deliveryAddress/462837512` (200) confirming both pushes reached Tripletex, plus matching Resco PATCH calls
- [x] 9.5 Created a product via `POST /products` with `product_type: "PRD"`, `number: "99999TEST"`; response shows `number: "PRD99999TEST"` (auto-prefixed), Tripletex id `91140762` adopted, `resco_product_id` populated. Also verified `PATCH /products/{id}` pushes `PUT /v2/product/{id}` (200).
- [x] 9.6 Soft-deleted all three (`DELETE`, all `204`); confirmed each absent from `GET /customers`, `/customer-locations`, `/products` immediately after
- [x] 9.7 Triggered `POST /customers/sync` and `POST /products/sync` (real full syncs, 200 each); confirmed all three test records still absent from their list endpoints afterward, and confirmed directly in the DB that each row has `delete_flag=False, archived=True` — Tripletex still had them (delete_flag never flipped) while the local soft-delete held, exactly the guarantee the `archived`/`delete_flag` split exists for
