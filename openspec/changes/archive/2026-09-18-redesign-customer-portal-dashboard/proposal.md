## Why

Today, once a specific customer is selected in the Customer Portal, their information is still spread across three separate tabs (a Customer detail page, a separate Customer Locations list, a separate Contracts list) with no single place to see "everything about this customer." A real customer logging in (once `add-user-authentication` ships) needs one page that shows what matters to them at a glance: their locations, their contracts, their upcoming visits, and a way to ask for something extra — without hunting across tabs built for staff browsing many customers at once.

## What Changes

- For a selected customer (today: via the admin switcher; once logged in as a customer: automatically), replace the separate Customer detail / Customer Locations / Contracts tabs with one consolidated dashboard page showing: that customer's locations, their contracts (with contract lines), and their upcoming planned service visits, all on one page.
- Add an "Offers" section to the dashboard as an explicit placeholder — a task-like reminder block that is empty today. No backend or data model for offers is added in this change; it's a visual stub for a future feature this proposal deliberately does not build.
- Add "extra services": a customer can browse the catalog of orderable extra products (Tripletex products of type `PRD`, distinct from the `TJN` products a contract already recurringly bills) and submit a request for one at a specific one of their locations. This creates a lightweight, staff-visible request record — it does not create a contract, a contract line, or a Tripletex order automatically.
- Admin browsing of "All customers" (the existing separate Customers/Customer Locations/Contracts list tabs) is unchanged — this only replaces what you see once you've drilled into one specific customer.

## Capabilities

### New Capabilities
- `service-requests`: a customer's request for an extra (non-contracted) product/service at one of their locations, and the staff-facing visibility into pending requests.

### Modified Capabilities
- `customer-portal`: selecting a specific customer now shows one consolidated dashboard (locations, contracts, planned visits, an offers placeholder, and the extra-services request flow) instead of three separate tabs for that customer.
- `admin-portal`: gains a Service Requests view for staff to see and acknowledge pending extra-service requests.

## Impact

- `backend/app/models.py`: new `ServiceRequest` model (`id`, `customer_id`, `customer_location_id`, `product_id` (the requested `PRD` product), an optional note, `status` (`pending`/`acknowledged`), `created_at`).
- `backend/app/schemas.py`, `backend/app/main.py`: `ServiceRequestOut`/`ServiceRequestCreate` schemas; `POST /service-requests` (customer-portal-facing, creates a request); `GET /service-requests` (staff-facing, lists pending/all requests) and `PATCH /service-requests/{id}` (mark acknowledged).
- An Alembic migration for the new `service_requests` table.
- `frontend/src/customer-portal/`: a new `CustomerDashboard.tsx` (or similar) replacing the per-customer view once a specific customer is in scope; the existing `CustomersView.tsx`/`CustomerLocationsView.tsx`/`ContractsView.tsx` remain for admin "All customers" browsing, unchanged.
- `frontend/src/types.ts`, `frontend/src/api.ts`: `ServiceRequest`/`ServiceRequestCreateInput` types and client functions.
- A small new Admin Portal view (or a section added to an existing one) for staff to see and acknowledge pending service requests — exact placement decided in design.md.

**Depends on nothing structurally**, but is designed to work identically whether "the current customer" comes from the Admin Portal's existing switcher (today) or from a real customer login (once `add-user-authentication` ships) — see design.md.
