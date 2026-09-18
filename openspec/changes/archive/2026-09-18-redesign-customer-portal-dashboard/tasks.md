## 1. Backend — service requests data model

- [x] 1.1 Add `ServiceRequest` model (`id`, `customer_id` FK, `customer_location_id` FK, `product_id` FK, `note` nullable, `status` enum `pending`/`acknowledged` default `pending`, `created_at` default now) to `backend/app/models.py`
- [x] 1.2 Add an Alembic migration creating `service_requests`. Migration `0023_service_requests.py` run successfully (0022 → 0023); confirmed the table is queryable.

## 2. Backend — service request endpoints

- [x] 2.1 Add `ServiceRequestOut`/`ServiceRequestCreate` schemas to `backend/app/schemas.py`. Also added `CustomerDashboardOut` here (used by task 3.1's endpoint) since it's the same kind of output schema.
- [x] 2.2 Add `POST /service-requests`: validates the location belongs to the given customer and the product is a non-deleted `PRD`-type product, then persists a pending request. Also checks the caller's own customer scope (admin unrestricted, customer session must own `customer_id`) via `require_session` + `customer_scope_ids`, since a real customer session must not be able to submit a request on another customer's behalf.
- [x] 2.3 Add `GET /service-requests` (optional `status` filter, defaulting to `pending`). Admin-only (`require_admin`); `status` query param defaults to `pending`.
- [x] 2.4 Add `PATCH /service-requests/{id}` to set status to `acknowledged`. Admin-only.

## 3. Backend — dashboard data endpoint

- [x] 3.1 Add `GET /customers/{customer_id}/dashboard` returning that customer's own fields, its customer locations, its contracts (with contract lines), and its service visits with `requested_date >= today`, ordered by date — assembled server-side in one call rather than left to the frontend to stitch together. Gated with `require_customer_access` (admin unrestricted, customer session only its own assigned customer(s)) — confirmed via the OpenAPI schema that `customer_id` correctly resolves as a shared path parameter between the route and the dependency.

## 4. Frontend — types and API client

- [x] 4.1 Add `ServiceRequest`/`ServiceRequestCreateInput` and a `CustomerDashboard` (or equivalent) type to `frontend/src/types.ts`
- [x] 4.2 Add `createServiceRequest`, `listServiceRequests`, `acknowledgeServiceRequest`, `getCustomerDashboard` client functions to `frontend/src/api.ts`

## 5. Frontend — customer dashboard

**Design gap found and resolved during implementation (before 5.1):** `GET /products` was gated `require_admin` by the just-applied `add-user-authentication` change, but the "extra services" catalog (5.3) needs a real customer session to list `PRD` products too — nothing in this proposal's tasks anticipated that interaction. Surfaced to the user and resolved: relaxed `GET /products` to `require_session`, with a non-admin caller's results filtered to `product_type == "PRD"` only (admin sessions, including Admin Portal's own Products view, remain unrestricted). Verified: admin session sees all 25 products; a customer session sees only (currently zero, since none exist yet) PRD-type ones.

- [x] 5.1 Create `frontend/src/customer-portal/CustomerDashboard.tsx`: fetches `getCustomerDashboard(customerId)`, renders locations, contracts (with contract lines), and upcoming visits sections on one page. Also reuses the existing "Book ad-hoc visit" control (exported `BookAdHocVisit`/`formatInterval` from `ContractsView.tsx`) inline per contract line — the ad-hoc-booking capability is an existing, unmodified requirement that would otherwise become unreachable once the dashboard replaces the old tabs for a scoped customer (see 5.4's note on why the tabs are replaced, not just the customer-detail view).
- [x] 5.2 Add the "Offers" placeholder section (task-like block, explicit "no offers yet" state)
- [x] 5.3 Add the "extra services" section: lists non-deleted `PRD`-type products, a form to pick one of the customer's locations, an optional note, and submit via `createServiceRequest`. Shows "No extra services are currently available" when the catalog is empty (currently always, since no PRD products exist yet in this dataset).
- [x] 5.4 Wire `CustomerDashboard` into `CustomerPortalApp.tsx` in place of the old Customer-detail-plus-separate-tabs flow whenever a specific customer is in scope (switcher selection today; the sole assigned customer once `add-user-authentication` ships). Followed design.md's explicit framing literally: "the old CustomerDetail + separate location/contract tabs" is what gets replaced — so a new `dashboardCustomerId` (admin: `viewingAsCustomerId`; non-admin: their sole assigned customer id, else `null`) now hides the entire Customers/Customer Locations/Contracts entity nav and renders only `CustomerDashboard` once set, rather than just swapping the old per-customer detail view. Within "All customers" browsing (`dashboardCustomerId === null`), clicking a customer row in the Customers tab still shows `CustomerDashboard` for that one customer (satisfying the delta spec's literal "whether from the Customers list or via the customer switcher"), without hiding the other two tabs — matching the still-unmodified customer-portal requirement that the switcher's selection leaves Customer Locations/Contracts unaffected. Removed now-dead `pendingLocationId`/`handleSelectLocation`/`onSelectLocation` plumbing (the old cross-link from a customer's detail view into the Customer Locations tab, superseded by the dashboard already showing locations inline). Verified via `npm run build`: zero errors.

## 6. Frontend — Admin Portal Service Requests view

- [x] 6.1 Create `frontend/src/admin-portal/ServiceRequestsView.tsx` (list of pending requests, acknowledge action)
- [x] 6.2 Wire it into `AdminPortalApp.tsx`'s entity list/nav. Verified via `npm run build`: zero errors.

## 7. Manual verification

- [x] 7.1 Select a specific customer via the switcher; confirm the dashboard shows their locations, contracts, and upcoming visits on one page, and no separate detail/tabs navigation is needed. Verified live in browser: selecting Bergsameie showed customer fields, Locations, Upcoming Visits, Contracts (with ad-hoc booking), Offers, and Request-an-Extra-Service, all on one page, with the Customers/Customer Locations/Contracts tabs correctly hidden.
- [x] 7.2 Confirm a customer with no upcoming visits shows an explicit "no upcoming visits" state, not a blank section. Verified live: selecting "Driven By Analytics AS" (a customer with no contracts at all) showed "No upcoming visits scheduled." (and correctly also "No locations on file." / "No contracts on file." for its other empty sections).
- [x] 7.3 Confirm the Offers section shows an explicit "no offers yet" placeholder. Verified live: "OFFERS / No offers yet — check back here later."
- [x] 7.4 Submit an extra-service request for a real `PRD` product and one of the customer's locations; confirm it appears in the Admin Portal's Service Requests view. No PRD products exist in this dataset, so a temporary one (`PRD99999`) was inserted directly into the local DB (bypassing `POST /products`, which pushes to the real Tripletex account and fails there with a permissions error). Verified live: submitted a request for Bergsameie / PRD99999 / Maridalsveien 58 through the actual dashboard form; it appeared correctly in the Admin Portal's Service Requests view with customer, product, location, and timestamp. (A first submit attempt via simulated pixel/ref clicks silently failed to fire — same click-simulation flakiness seen earlier this session on this UI; switched to a direct JS `.click()` on the submit button, which worked and is the reliable method going forward for this codebase's forms.)
- [x] 7.5 Attempt to submit a request naming a location that belongs to a different customer; confirm it is rejected. Verified live via a direct authenticated `fetch`: `POST /service-requests` with Bergsameie's `customer_id` but another customer's `customer_location_id` → 422 "Customer location does not belong to the given customer" (also covered by the earlier automated smoke test).
- [x] 7.6 Acknowledge a request from the Admin Portal; confirm it disappears from the pending list. Verified live: clicking "Acknowledge" removed it from the pending list ("No pending service requests." shown), and its DB status persisted as `acknowledged`.
- [x] 7.7 Confirm admin "All customers" browsing (the three original tabs) is unchanged. Verified live: with the switcher on "All customers", the Customers, Customer Locations, and Contracts tabs all still show their full, unfiltered lists across every customer, exactly as before this change.
