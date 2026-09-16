## Why

Customer, customer location, and product records are currently 100% read-only in fms_ros — entirely sourced from Tripletex, with no create/update/delete path of any kind locally. Going forward, fms_ros needs to be the authoring system for this masterdata: staff create and edit customers, locations, and products directly in fms_ros, which then pushes new/changed records out to Tripletex (and, where applicable, Resco) rather than only pulling them in.

## What Changes

- **BREAKING**: Customer, customer location, and product records become creatable and editable in fms_ros, not just Tripletex-sourced read models. Tripletex sync (and, for customers/locations, the existing Resco sync) continues to run and still reconciles records Tripletex itself changes, but no longer the only way a record comes into existence.
- Creating a customer, customer location, or product in fms_ros pushes it to Tripletex first and adopts Tripletex's returned id as the record's own id (mirroring how these ids already work — Tripletex's id has always been the primary key). Updating a locally-created-or-synced record pushes the change back to Tripletex.
  - Customers additionally get pushed to Resco as an Account and products to Resco as a Product, reusing the existing Resco sync plumbing (customer locations already push to Resco as Assets).
  - A customer location's "create" path is a genuinely new Tripletex operation (no location has ever been created *from* fms_ros before) — see design.md for how this is verified against Tripletex's actual API before being relied on.
- Soft-delete stays the deletion model for all three (matching every other entity in this codebase); nothing is ever hard-deleted or removed from Tripletex/Resco by fms_ros.
- The Admin Portal's Customers, Customer Locations, and Products views gain create/edit/soft-delete forms (Customers and Products are currently fully read-only; Customer Locations only has the coordinate-override form).
- Existing data is unaffected: every currently-synced customer/location/product already carries Tripletex's real id as its primary key, so nothing needs to be re-created or re-seeded — the only change is that new records can now originate in fms_ros instead of only arriving via Tripletex sync.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `customers`: customer and customer-location data models gain a locally-initiated create/update path that pushes to Tripletex (customers also to Resco, already specified in `resco-integration`).
- `products`: product data model gains a locally-initiated create/update path that pushes to Tripletex and Resco.
- `admin-portal`: Customers, Customer Locations, and Products views gain create/edit/soft-delete controls.
- `resco-integration`: gains product→Resco-Product sync, following the same upsert-by-remembered-id pattern as customers/locations/employees.

## Impact

- `backend/app/models.py`: `Customer`, `CustomerLocation`, `Product` gain nothing new schema-wise beyond `Product.resco_product_id` (mirroring `resco_account_id`/`resco_asset_id`) — everything else needed (Tripletex id as primary key, soft-delete flag) already exists.
- `backend/app/tripletex.py`: new `create_product`/`update_product` client methods; a customer-location create path (mechanism to be confirmed live — see design.md); `create_customer` already exists and is reused for customer creation.
- `backend/app/resco.py`: new `create_product`/`update_product` Resco methods and `sync_product`/`sync_products_to_resco`, mirroring the customer/location sync functions.
- `backend/app/schemas.py`, `backend/app/main.py`: new `CustomerCreate`/`CustomerUpdate`, `CustomerLocationCreate`/`CustomerLocationUpdate`, `ProductCreate`/`ProductUpdate` schemas and their endpoints (POST/PATCH/DELETE for each of the three entities).
- `frontend/src/admin-portal/`: `CustomersView.tsx`, `CustomerLocationsView.tsx`, `ProductsView.tsx` gain create/edit/soft-delete forms, following the existing Employee/Region form patterns.
- `frontend/src/api.ts`, `frontend/src/types.ts`: new create/update/delete client functions and input types for all three entities.

**Assumption (design.md elaborates):** the exact Tripletex API mechanism for creating a *new* delivery address for an *existing* customer (as opposed to one created alongside a brand-new customer) is unconfirmed — Tripletex's own API documentation comment already on file notes delivery-address creation as a side effect of customer creation, not a standalone operation. This is verified live as an early implementation task before the rest of customer-location creation is built on top of it.
