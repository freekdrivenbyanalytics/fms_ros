## Why

Technicians need customers and their equipment/sites visible in Resco (as Accounts and Assets) so field work can be logged against them, but there's no connection between fms_ros's Tripletex-sourced customer data and Resco today. Live verification against the real Resco OData API and the real Tripletex data shows Resco's Account entity wants email, phone, address, and a VAT/org number — none of which any of this org's 150 Tripletex customers currently have populated (only `name` is reliably present). Since Tripletex customer records can be updated via its API, the fix is to seed that missing contact/address data directly into Tripletex — keeping it as the single source of truth — rather than maintaining a second, locally-edited copy in fms_ros.

## What Changes

- Add a new Resco Account sync: each customer is pushed to Resco as an Account (name, email, phone, VAT/org number, address), matching the pattern already established for employees → Resco Users. The address comes from the customer's existing customer location (see below), not from a new Tripletex field.
- Add a new Resco Asset sync: each customer location is pushed to Resco as an Asset (name = the location's address, linked to its customer's Resco Account), since the customer relationship is what's needed and Resco's Asset entity has no address fields of its own.
- One-time data fix: generate a CSV of realistic email/phone/org-number values for this sandbox's ~150 existing demo customers, and a script that pushes those values into the corresponding Tripletex customer records via its API. This is a one-off implementation task, not a permanent tool — once run, the normal Tripletex sync picks the data up like any other Tripletex-sourced field. **The script deliberately never writes a customer-level address to Tripletex** — an earlier version did, and discovered that Tripletex's customer-update API creates a duplicate delivery address (customer location) as an unintended side effect; that data was cleaned up and the design changed to source the Resco Account's address from the customer's existing (real) customer location instead (design.md elaborates).
- Both Resco syncs run automatically right after their respective Tripletex sync (startup and on-demand) completes, and are also each triggerable manually via a "Sync to Resco" button — matching the employee integration's automatic + manual pattern. A location whose customer hasn't been synced to Resco yet (no Resco Account id), or that has no street address, is skipped and reported.
- Add a new, read-only "Customers" view to the Admin Portal (it doesn't have one today) so staff can see each customer's Tripletex-sourced data and its Resco sync status.

## Capabilities

### New Capabilities
(none — this extends the `resco-integration` capability added for employees)

### Modified Capabilities
- `resco-integration`: gains customer→Account and customer-location→Asset sync, following the same skip/report/upsert-by-remembered-id pattern as the employee→User sync.
- `customers`: customer data model gains a remembered `resco_account_id`; customer locations gain a remembered `resco_asset_id`.
- `admin-portal`: gains a new, read-only Customers view.

## Impact

- `backend/app/models.py`: `Customer` gains `resco_account_id`; `CustomerLocation` gains `resco_asset_id`. New Alembic migrations (including one that added, then a follow-up that dropped, a customer-level address that turned out to be the wrong approach — see design.md).
- `backend/app/tripletex.py`: a new `update_customer` client method (not currently present — only create/delete exist) to support the one-time contact-data seeding, sending only `email`/`phoneNumber`/`organizationNumber` (never a customer-level address — see design.md).
- `backend/app/resco.py`: extended with Account and Asset create/update methods and `sync_customer`/`sync_customer_locations_to_resco`-style functions, mirroring the existing employee sync functions. The Account's address is read from the customer's existing `CustomerLocation`.
- `backend/app/schemas.py`, `backend/app/main.py`: `POST /customers/sync-resco` and `POST /customer-locations/sync-resco`.
- A one-off script + CSV (`backend/scripts/`) to seed Tripletex's existing customers with email/phone/org-number data — run once, not wired into `seed.py` or backend startup.
- `frontend/src/admin-portal/`: new read-only `CustomersView.tsx` (list, detail, "Sync to Resco" button), wired into `AdminPortalApp.tsx`.
- `frontend/src/api.ts`, `frontend/src/types.ts`: new sync-resco client functions/types.

**Resolved during implementation (design.md elaborates):** (1) the OData syntax for writing an Asset's Account link, verified live: `{"customerid_account@odata.bind": "/account({id})"}`; (2) Tripletex's customer-update API shape, verified live — `email`/`phoneNumber`/`organizationNumber` are freely editable, but a `physicalAddress` write has a real, unwanted side effect (creates a duplicate delivery address) that led to a mid-implementation design change — see design.md's Context and Risks sections for the full incident and cleanup.
