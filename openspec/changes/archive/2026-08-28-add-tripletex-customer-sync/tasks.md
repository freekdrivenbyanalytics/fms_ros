## 1. Setup and Discovery

- [x] 1.1 Create `backend/.local/api_key` (gitignored) holding the Tripletex refresh token; add `.local/` to `backend/.gitignore`.
- [x] 1.2 Add `httpx` to `backend/requirements.txt` and install it.
- [x] 1.3 Add `tripletex_base_url` and `tripletex_session_ttl_seconds` to `Settings` in `backend/app/config.py`, sourced from `.env` like `database_url`.
- [x] 1.4 Implement a minimal `TripletexClient` (e.g. `backend/app/tripletex.py`) covering only the auth exchange (`POST {base_url}/token/session/:createFromRefreshToken` with the refresh token and `ttlSeconds`, caching the session token in memory until shortly before expiry) and a raw customer-list call using HTTP Basic auth (username `"0"`, password the session token).
- [x] 1.5 Using `TripletexClient`, make one real call to Tripletex's customer endpoint and record the actual response shape (field names, types, which are nested/list-valued) — this determines the columns added in task 2.

## 2. Data Model

- [x] 2.1 Update `Customer` in `backend/app/models.py` to match the discovered Tripletex fields: `id` becomes a non-autoincrement Integer primary key; flat scalar fields become typed columns; nested/list-valued fields become `JSONB` columns.
- [x] 2.2 Add a `delete_flag` boolean column (default `False`, not nullable) to `Customer` in `backend/app/models.py`.
- [x] 2.3 Add a `CustomerSyncLog` model in `backend/app/models.py`: `id` (autoincrement PK), `customer_id` (FK to `customers.id`), `change_type` (enum: `created`/`updated`/`deleted`/`restored`), `occurred_at` (timestamp, server default now).
- [x] 2.4 Write an Alembic migration that: truncates `customer_locations`, `contracts`, `service_visits`, and `assignments`; drops `customers.id`'s SERIAL default/sequence; alters `customers` to the new column set including `delete_flag`; creates the `customer_sync_log` table. Include a downgrade that restores the previous `{id (autoincrement), name}` shape and drops `customer_sync_log`.
- [x] 2.5 Update `CustomerOut` in `backend/app/schemas.py` to match the new `Customer` fields.

## 3. Sync Logic

- [x] 3.1 Extend `TripletexClient` to fetch the full customer list (handling pagination if Tripletex's customer endpoint paginates).
- [x] 3.2 Implement `sync_customers(db)` (e.g. in `backend/app/tripletex.py`): fetch all Tripletex customers, insert ones not yet persisted locally, update fields on ones that already exist, set `delete_flag=True` on local customers no longer present in Tripletex, and clear `delete_flag` (and refresh fields) on a previously-flagged customer that reappears. For each of these four outcomes, write a matching `CustomerSyncLog` row (`created`/`updated`/`deleted`/`restored`) in the same transaction.
- [x] 3.3 Add a FastAPI startup hook (lifespan) in `backend/app/main.py` that calls `sync_customers(db)` inside a try/except, logging a warning and continuing startup on failure (missing key file, unreachable Tripletex, etc.).
- [x] 3.4 Add `POST /customers/sync` to `backend/app/main.py`, calling `sync_customers(db)` and letting failures surface as a 502 (no silent failure for an explicit, user-triggered call).
- [x] 3.5 Update `GET /customers` (`list_customers`) in `backend/app/main.py` to exclude customers with `delete_flag=True`.

## 4. Seed Script

- [x] 4.1 Update `backend/app/seed.py` to call `sync_customers(db)` first (instead of creating `Customer` rows itself), then query the resulting customers ordered by `id` ascending.
- [x] 4.2 Attach the existing fixture `CustomerLocation`/`Contract`/`ServiceVisit` data (unchanged in shape/values otherwise) to the first three synced customers, positionally (per confirmed decision — only 3 real Tripletex customers exist, so the `visser` fixture is dropped; `de_jong`'s 2-location fixture is kept as the third customer's data).

## 5. Frontend

- [x] 5.1 Update `Customer` in `frontend/src/types.ts` to match the new `CustomerOut` fields.
- [x] 5.2 Add `syncCustomers()` to `frontend/src/api.ts` (`POST /customers/sync`).
- [x] 5.3 Add a "Refresh" button to the unscoped Customers list view in `frontend/src/customer-portal/CustomersView.tsx` that calls `syncCustomers()`, then triggers re-fetching customers, customer locations, and contracts (via callbacks from `CustomerPortalApp.tsx`).
- [x] 5.4 Update the Customers list columns and detail view in `CustomersView.tsx` to show the newly available Tripletex-sourced fields (a curated, business-relevant subset — ID, name, customer number, email, phone on the list; those plus organization number, invoice email, mobile, language, type flags, and website on detail — rather than all ~40 raw fields, to keep the view "simple, clean" per the portal's original design intent).

## 6. Verification

- [x] 6.1 Run `alembic upgrade head`, then `python -m app.seed`, and confirm the `customers` table is populated from Tripletex with the new fields, and that locations/contracts/visits are attached to the first three synced customers (only 3 real Tripletex customers exist — see task 4.2).
- [x] 6.2 Start the backend without `backend/.local/api_key` present and confirm it still starts successfully (logs a warning, serves requests with whatever customer data already exists locally).
- [x] 6.3 Start the backend with a valid key and confirm the startup log shows a successful sync.
- [x] 6.4 Call `POST /customers/sync` directly and confirm it reconciles correctly: a customer added in Tripletex appears locally, a changed field is updated locally, and (if testable) a customer removed from Tripletex is marked `delete_flag=True` locally — with its locations/contracts/visits/assignments left intact and `GET /customers` no longer listing it — and reappears (flag cleared) if added back in Tripletex before a later sync. (Verified created/updated/deleted/restored via a locally simulated Tripletex response rather than mutating the real Tripletex demo account; the endpoint itself verified directly via `curl`.)
- [x] 6.5 In the Customer Portal, confirm the Customers list/detail show the new fields, and that clicking Refresh re-syncs and updates the Customers, Customer Locations, and Contracts views.
- [x] 6.6 Confirm no Tripletex credential or session token ever appears in any response the frontend receives (inspect network requests from the browser).
- [x] 6.7 Confirm the existing Planning app and Day Planning view still work unchanged against the newly synced customer data.
- [x] 6.8 After the syncs run in 6.1/6.4, inspect `customer_sync_log` and confirm it has one row per customer creation, update, delete, and restore that occurred, each with the correct `change_type` and a populated `occurred_at`.
