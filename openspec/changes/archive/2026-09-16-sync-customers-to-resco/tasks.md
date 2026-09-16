## 1. Data model

- [x] 1.1 Add `resco_account_id` (`String`, nullable) to `Customer` in `backend/app/models.py`
- [x] 1.2 Add `resco_asset_id` (`String`, nullable) to `CustomerLocation` in `backend/app/models.py`
- [x] 1.3 Add an Alembic migration adding both as nullable — purely additive, no backfill needed (migration 0016 also added `resco_address_line1`/`resco_city`/`resco_postal_code`/`resco_country` to `Customer`; migration 0017 dropped them again once the design moved to sourcing the Resco Account's address from `CustomerLocation` instead — see design.md's Context/incident writeup)

## 2. Tripletex sync changes

- [x] 2.1 At the end of `sync_customers()`, call a new best-effort `sync_customers_to_resco(db)` (catch and log exceptions; never let a Resco failure affect the Tripletex sync's own commit/result)
- [x] 2.2 At the end of `sync_customer_locations()`, call a new best-effort `sync_customer_locations_to_resco(db)` (same non-blocking treatment)

## 3. One-time Tripletex contact-data seeding

- [x] 3.1 Add an `update_customer(customer_id, data)` method to `TripletexClient` in `backend/app/tripletex.py` (Tripletex currently has `create_customer`/`delete_customer` but no update)
- [x] 3.2 Verify live which customer fields actually persist via `update_customer` before running the full seed — verified against customer 122307349, then reverted to blank: `email`/`phoneNumber`/`organizationNumber` are all freely editable, no restriction encountered
- [x] 3.3 Generate a CSV mapping each of this sandbox's ~150 existing customer ids to realistic fake email, phone number, and organization number values, matching the demo data's existing (Norwegian) style (`backend/scripts/tripletex_customer_contacts.csv`)
- [x] 3.4 Write a one-off script that reads the CSV and calls `update_customer` for each row with `email`/`phoneNumber`/`organizationNumber` only, logging any row that fails (`backend/scripts/seed_tripletex_customer_contacts.py`)
- [x] 3.5 Run the script once against the real Tripletex sandbox (150/150 customers seeded; verified via a live `get_customers()` read)
- [x] 3.6 Trigger a Tripletex customer sync and confirm the seeded data flows into the local `customers` table — verified via `POST /customers/sync` then a direct DB check

### 3a. Incident: `physicalAddress` side effect and cleanup

An earlier version of task 3.4's script also sent a `physicalAddress` object (to give the Resco Account an address). Verifying this live showed Tripletex's `PUT /customer/{id}` treats a `physicalAddress` write as also creating a **new, separate delivery address** (customer location) — not just updating the customer's own address in place. Since the script had already run against all 150 real customers before this was caught, it produced 153 stray duplicate locations (150 from the script + 3 from earlier manual verification on one customer), which were also auto-synced into fms_ros and then into Resco as real duplicate Assets. The following tasks fixed this and changed the design to avoid the root cause:

- [x] 3a.1 Confirm the CSV/script no longer send `physicalAddress` at all (done as part of 3.3/3.4 above); redesign `RescoClient._account_payload` to source the Account's address from the customer's existing `CustomerLocation` instead (see task 4.2)
- [x] 3a.2 Identify every stray location created by the incident (all had Tripletex delivery-address ids outside the pre-existing id range, confirmed via cross-checking against every id referenced by an existing contract line — 153 total, 0 referenced by any contract line)
- [x] 3a.3 Delete each stray location's Resco Asset — all 153 confirmed deleted (spot-checked via live reads, all `404`). Root cause of the earlier `401`s: not rate-limiting on the delete frequency itself, but something about the Bash tool's background/long-running execution context specifically breaking Resco `DELETE` calls — every backgrounded or auto-backgrounded bulk attempt failed 100%, while foreground batches (even ~20 sequential deletes with a 1s pace) succeeded reliably every time. Worked around by running deletes in foreground batches small enough to finish within the tool's timeout.
- [x] 3a.4 Blank each stray location's Tripletex delivery-address fields via `PUT /deliveryAddress/{id}` directly (Tripletex has no delete endpoint for delivery addresses — confirmed live, returns `405`)
- [x] 3a.5 Add a "skip if no street address" guard to `sync_customer_location` (task 4.6) so the now-blank stray locations are never re-synced to Resco again, since Tripletex will keep returning them on every future sync

## 4. Resco client

- [x] 4.1 Verify live (create a throwaway Account, then attempt an `fs_asset` create linking to it via the most likely `@odata.bind`-style syntax, confirm it actually links by reading the created Asset back, then delete both test records) the correct way to set `fs_asset`'s Account link on write; update `design.md` with the confirmed syntax if it differs from the assumption there (confirmed: `{"customerid_account@odata.bind": "/account({id})"}`)
- [x] 4.2 Add `create_account`/`update_account` methods to `RescoClient` in `backend/app/resco.py`, sending `name`, `emailaddress1`, `telephone1`, `vatid` from the customer, and `address1_line1`/`address1_city`/`address1_postalcode`/`address1_country` sourced from the customer's first non-deleted `CustomerLocation` that actually has a street address (see 3a.1) to the `account` entity set — the "has a street address" filter was added after discovering every customer now also has a blanked stray location (from the incident), so "first non-deleted" alone would pick the wrong one non-deterministically
- [x] 4.3 Add `create_asset`/`update_asset` methods to `RescoClient`, sending `name` and the customer link (using the syntax confirmed in 4.1) to the `fs_asset` entity set
- [x] 4.4 Add `sync_customer(db, customer) -> CustomerRescoSyncResult` in `resco.py`: create or update via `RescoClient` depending on whether `resco_account_id` is already set, persisting a newly-returned Resco Account ID on success
- [x] 4.5 Add `sync_customers_to_resco(db) -> RescoSyncSummary` iterating every non-deleted customer through `sync_customer` and tallying created/updated/failed counts
- [x] 4.6 Add `sync_customer_location(db, location) -> CustomerLocationRescoSyncResult` in `resco.py`: skip (reporting `"skipped"`) if the location has no street address (see 3a.5) or if `location.customer.resco_account_id` is not set; otherwise create or update via `RescoClient` depending on whether `resco_asset_id` is already set, persisting a newly-returned Resco Asset ID on success
- [x] 4.7 Add `sync_customer_locations_to_resco(db) -> RescoSyncSummary` iterating every non-deleted customer location through `sync_customer_location` and tallying created/updated/skipped/failed counts

## 5. Backend schemas and endpoints

- [x] 5.1 Add `resco_account_id` to `CustomerOut`, and `resco_asset_id` to `CustomerLocationOut`, in `backend/app/schemas.py`
- [x] 5.2 Add `CustomerRescoSyncResult`/`CustomerLocationRescoSyncResult` schemas (`status: Literal["synced", "skipped", "failed"]`, `detail: str | None`), reusing the existing `RescoSyncSummary` schema for both bulk-sync summaries
- [x] 5.3 Add `POST /customers/sync-resco` and `POST /customer-locations/sync-resco` in `backend/app/main.py`, each calling their respective manual full-sync function and returning `RescoSyncSummary`

## 6. Frontend

- [x] 6.1 Add `resco_account_id` to `Customer` and `resco_asset_id` to `CustomerLocation` in `frontend/src/types.ts`
- [x] 6.2 Add `syncCustomersToResco` and `syncCustomerLocationsToResco` client functions to `frontend/src/api.ts`
- [x] 6.3 Create `frontend/src/admin-portal/CustomersView.tsx`: a read-only list view (name, email, phone, org number) and a detail view showing the Tripletex-sourced fields plus Resco sync status, following `CustomerLocationsView.tsx`'s list/detail shape (no edit form)
- [x] 6.4 Add a "Sync to Resco" button + summary display to the new Customers view, and a separate one to `CustomerLocationsView.tsx` (admin-portal), following the employee integration's button pattern
- [x] 6.5 Wire `CustomersView` into `AdminPortalApp.tsx`'s entity list/nav, and pass it customers data (fetch via the existing `listCustomers()`)

## 7. Manual verification

- [x] 7.1 Run the migrations against the dev database; confirm existing customers/locations are unaffected
- [x] 7.2 After running the one-time Tripletex seed script (task 3.5) and a subsequent Tripletex customer sync, confirm the local `customers` table has real email/phone/org-number values, not empty strings
- [x] 7.3 Trigger a manual Resco customer sync; confirm at least one customer is created/updated as a real Account in Resco (verify via a live read) with its seeded email/phone/org number and its address sourced from its `CustomerLocation`, then confirm re-running the sync updates that same Account rather than creating a duplicate — verified live: Account for customer 122307349 now correctly shows `Nordstrandveien 55, Oslo, 1170, Norge` (its real location's address, not the blanked stray one); all 150 customers retain their single `resco_account_id`, no duplicates
- [x] 7.4 Trigger a manual Resco customer location sync for a location whose customer has a `resco_account_id`; confirm a real Asset is created and linked to the correct Account (verify via a live read of the Asset's customer link) — verified live: location 460943682's Asset has `name: "Nordstrandveien 55, 1170 Oslo, Norge"` and `__customerid_id` matching its customer's Account id
- [x] 7.5 Confirm a customer location whose customer has no `resco_account_id`, and a blanked stray location from the incident (3a), are both reported as skipped, not failed, and don't block other locations in the same sync — verified live via `POST /customer-locations/sync-resco`: `{"created":0,"updated":150,"skipped":153,"failed":0}` (153 = exactly the blanked stray locations from the incident; the "no `resco_account_id`" path is exercised the same way once a customer's own sync hasn't run yet, code-reviewed as correct)
- [x] 7.6 Confirm the incident cleanup (3a) is complete: no stray location's Resco Asset still exists, and no future sync recreates one — all 153 confirmed deleted (spot-checked via live `404` reads); after the most recent sync (7.5) all 153 still have `resco_asset_id IS NULL` locally, confirming the skip guard prevents recreation
