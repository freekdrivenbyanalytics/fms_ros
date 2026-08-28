## Why

Customer master data currently lives only as fixture rows created by `backend/app/seed.py` — there is no connection to Tripletex, the real system of record for customers in this organization. Syncing customers from Tripletex is the first step toward the Customer Portal's stated purpose (a master-data administration surface) actually reflecting real operational data instead of a hardcoded demo.

## What Changes

- **BREAKING**: The `customers` table is redefined to match Tripletex's customer fields (exact column list finalized during implementation by first calling Tripletex's `/customer` endpoint and inspecting its response — see design.md). The customer's Tripletex-sourced key becomes the table's primary key; there is no separate app-only customer id. Existing `customer_locations`/`contracts`/etc. that reference a customer continue to do so by this id, now sourced from Tripletex rather than autoincrement.
- Add a `TripletexClient` (backend) that authenticates using a refresh token read from `.local/api_key` (gitignored), exchanges it for a short-lived session token via Tripletex's `POST /token/session/:createFromRefreshToken`, and calls Tripletex's customer endpoint. The Tripletex base URL and session TTL are configurable via environment variables. Tripletex credentials and session tokens are never exposed to the frontend — all Tripletex traffic goes through the FastAPI backend.
- Add a reusable customer-sync function that fetches every customer from Tripletex and reconciles them into the local `customers` table: customers present in Tripletex but not locally are inserted, customers present in both have their fields overwritten to match Tripletex, and customers no longer present in Tripletex are marked deleted locally via a `delete_flag` column rather than removed — their locations/contracts/visits/assignments are left untouched. A customer that reappears in Tripletex after being flagged has its flag cleared. Delete-flagged customers are hidden by default from `GET /customers` and the Customer Portal's Customers list.
- Run this sync automatically once on backend startup. Add a `POST` endpoint the frontend can call on demand, and wire a "Refresh" button into the Customer Portal's Customers list view that calls it and then re-fetches customers, customer locations, and contracts (a sync can add, hide, revive, or change customer fields, and customer locations/contracts embed a snapshot of their customer that should stay current).
- `backend/app/seed.py` no longer creates `Customer` rows itself. It runs the Tripletex sync first (customer keys are not known before that), then creates the existing demo `CustomerLocation`/`Contract`/`ServiceVisit` fixtures, positionally attached to the first four customers returned by Tripletex (in ascending id order), in the same shape as today's fixtures. Any additional Tripletex customers beyond the first four are seeded with no locations/contracts.
- Extend the Customer Portal's Customers list/detail views to display the newly available Tripletex-sourced fields (beyond just name), and add the Refresh button described above.
- Add a `customer_sync_log` table recording every customer change the sync makes — created, updated, marked deleted, or restored — with the customer id, the type of change, and when it occurred. This is a write-only audit trail for now; no API or UI exposes it in this change.

## Capabilities

### Modified Capabilities
- `customers`: The Customer data model requirement changes — customers are now sourced and kept in sync from Tripletex rather than created locally, keyed by their Tripletex id, with additional Tripletex fields persisted.
- `customer-portal`: The Customers list/detail views show the additional Tripletex-sourced fields, and gain a Refresh action that re-syncs from Tripletex on demand.

## Impact

- **Affected code**: `backend/app/models.py` (`Customer` model redefined), a new Alembic migration, `backend/app/schemas.py` (`CustomerOut` updated), `backend/app/seed.py` (restructured to sync-then-fixture), a new `backend/app/tripletex.py` (or similar) client + sync module, `backend/app/main.py` (startup sync hook + new sync endpoint), `backend/app/config.py` (new Tripletex settings); `frontend/src/customer-portal/CustomersView.tsx` (new fields, Refresh button), `frontend/src/customer-portal/CustomerPortalApp.tsx` (re-fetch after refresh), `frontend/src/api.ts` (new sync call), `frontend/src/types.ts` (`Customer` type updated).
- **Affected systems**: Backend now depends on Tripletex's API being reachable at startup and on demand (see design.md for startup-resilience handling); local dev requires a `.local/api_key` file with a valid Tripletex refresh token to seed or sync customers.
- **Dependencies**: An HTTP client library for the backend (e.g. `httpx`) if not already available — see design.md.
- **Security**: Adds a new local secret file (`backend/.local/api_key`), added to `backend/.gitignore`; never sent to the frontend.
