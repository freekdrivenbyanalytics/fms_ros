## Why

The current seed data (a handful of hardcoded customers, contract lines, and employees) is too small and too synthetic to stress-test scheduling, routing, and the Admin Portal under realistic load. The business wants a repeatable way to reset the demo environment to a larger, more realistic scenario — around 150 customers spread across Oslo and Akershus — so the solver, regions, and planning views can be exercised the way they would be with a real customer base.

## What Changes

- Add a new standalone script (run like the existing `python -m app.seed`) that resets and reseeds the demo environment in one pass:
  1. Requires an explicit confirmation flag before doing anything destructive (e.g. `--confirm`), since it deletes real data in the connected Tripletex account.
  2. Deletes every customer in the connected Tripletex account via the Tripletex API; each customer's delivery address is cascaded away with it (Tripletex has no standalone delivery-address delete endpoint). A customer that fails to delete — e.g. Tripletex's own built-in sample company, which carries baked-in ledger history the API won't let go of — is logged and skipped rather than aborting the run. Products are left untouched.
  3. Hard-deletes, locally, every service visit, assignment, contract, contract line, customer, and customer location (not soft-delete — the Tripletex-side data they mirror is gone too).
  4. Creates fresh customers and customer locations in Tripletex from a bundled CSV, via new Tripletex API write support (`create_customer`, with the delivery address embedded in the same call — Tripletex has no standalone delivery-address create endpoint either).
  5. Runs the existing Tripletex→local sync (`sync_customers`/`sync_customer_locations`) to pull the newly created data back into the local database, exactly as it does today on startup or on-demand.
  6. Seeds contracts and contract lines locally from a second bundled CSV, linking each contract line to its synced customer location and to one of four existing products (`TJN10001`-`TJN10004`, chosen once at random per line), then generates each line's unassigned service visits using the existing `generate_occurrence_dates` logic (the same function `POST /contract-lines` already uses) — no new visit-generation logic.
  7. Updates the product portfolio of every employee that already exists in the system (employees themselves are not deleted or reseeded): every employee is assigned all four demo products (`TJN10001`-`TJN10004`) except one designated employee, who is assigned all but `TJN10004`.
- Bundle two CSV files with the demo scenario's data, generated once as part of this change: customer/customer-location master data (~150 customers, addresses concentrated mostly in Oslo with the remainder in Akershus, geocoded via the existing TomTom integration so coordinates are realistic) and contract-line data (one contract line per customer location, a 15-day interval so each customer gets two visits a month, and its randomly-assigned product).
- Out of scope, left as manual follow-up steps (per the request): drawing/adjusting region geo-shapes to cover the new customer spread, and running the solver to actually plan the generated visits.

## Capabilities

### New Capabilities
- `demo-data-reset`: a standalone, explicitly-confirmed script that resets the Tripletex-connected demo environment (customers/customer-locations only) and the local database, then reseeds both from bundled CSV master data, reusing the existing Tripletex sync and visit-generation logic rather than duplicating it.

### Modified Capabilities
(none — no existing capability's requirements change; the Tripletex sync and visit-generation behaviors this script calls are unchanged, and the new Tripletex create/delete client operations are net-new, used only by this script)

## Impact

- `backend/app/tripletex.py`: new `TripletexClient.create_customer`/`delete_customer` methods (POST/DELETE), following the existing GET methods' auth pattern. No separate delivery-address create/delete methods — Tripletex has no such endpoints; a delivery address is created via a `deliveryAddress` field embedded in `create_customer`'s payload and removed via the owning customer's cascade on delete. No changes to the existing sync functions.
- New `backend/app/reset_demo_data.py` (or similar): the script itself, orchestrating the delete → Tripletex-create → sync → local-seed → visit-generation sequence, reusing `sync_customers`, `sync_customer_locations`, and `generate_occurrence_dates` directly.
- New bundled CSV data files under the backend app (e.g. `backend/app/demo_data/customers.csv`, `backend/app/demo_data/contract_lines.csv`), generated once as part of this change using the existing TomTom integration to resolve realistic Oslo/Akershus addresses and coordinates.
- No frontend changes, no database schema changes, no changes to existing API endpoints.
