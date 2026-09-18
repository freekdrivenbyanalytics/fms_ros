## Context

`CustomerPortalApp.tsx` already has a `viewingAsCustomerId: number | null` switcher (default "All customers") and already fetches `listServiceVisits()`, with `customer-portal/ContractsView.tsx` already cross-referencing service visits per contract line. There is no "offers" or "extra services" concept anywhere in the codebase today (confirmed via a repo-wide case-insensitive grep for "offer"/"tilbud" — zero matches). `Product.product_type` (`TJN`/`PRD`, added in `add-master-data-crud`) already distinguishes recurring-service products from standalone ones; nothing currently reads `PRD` products for anything.

## Goals / Non-Goals

**Goals:**
- One page per customer showing locations, contracts, and upcoming visits together.
- A working, if deliberately minimal, "request an extra service" flow with real staff-facing visibility.
- Works identically regardless of whether "the current customer" comes from today's admin switcher or from a real customer login (`add-user-authentication`, independent of this change).

**Non-Goals:**
- Building the actual "offers" feature (what an offer is, how it's generated from visits) — only a visual placeholder ships here.
- Any automated fulfillment of a service request (no contract/contract-line/Tripletex-order creation) — it is purely a staff-visible note-taking mechanism for this iteration.
- Changing admin "All customers" list browsing — those three tabs are untouched.

## Decisions

**The dashboard is driven by whatever `viewingAsCustomerId` (or, after `add-user-authentication`, the logged-in customer's id) already resolves to — no new "current customer" concept is introduced.** `CustomerPortalApp.tsx` already computes this value today for the switcher; this change only changes what renders once a specific id is selected (a new `CustomerDashboard.tsx` instead of the old `CustomerDetail` + separate location/contract tabs). This is why the change has no hard dependency on `add-user-authentication`: it consumes the exact same "which customer" signal that already exists, whichever mechanism produced it.

**"Extra services" reuses `Product.product_type == "PRD"` as the orderable catalog, instead of a new "is this orderable" flag.** `PRD` ("produkt") was already introduced as the counterpart to `TJN` ("tjeneste", the recurring contracted kind) specifically to distinguish one-off products from contract services — this is exactly that distinction, reused rather than duplicated.

**A service request is a plain, unopinionated record — no workflow beyond `pending`/`acknowledged`.** No customer-facing status tracking, no notifications, no SLA. This matches the proposal's explicit scope ("it does not create a contract... only a locally visible request for staff follow-up") and keeps the feature reviewable/buildable in the same pass as the dashboard itself rather than becoming its own mini order-management system.

**Service Requests gets a new, small Admin Portal view, not a bolt-on to an existing one.** Contracts/Products views are both about existing committed relationships; a pending request is a different kind of thing (unconfirmed, awaiting staff action) and deserves its own short list rather than being buried as a sub-section of something else. Follows the same list/acknowledge shape as every other simple entity view added so far (Skills, Service Order Types).

## Risks / Trade-offs

**Upcoming-visits query (today or later, across all of a customer's contract lines) needs to join through contract → contract lines → service visits, filtered by date — this is a new read pattern, not something an existing endpoint already returns pre-shaped this way.** → A new `GET /customers/{id}/dashboard` (or equivalent) endpoint assembles this server-side in one call, rather than the frontend stitching together `listContracts()` + `listServiceVisits()` + client-side filtering/joining, keeping the "one page, one load" goal fast and simple to reason about.

**The "Offers" placeholder risks looking like a real, unfinished feature if not visually distinct from the rest of the dashboard.** → Explicitly styled as a stub with a "nothing here yet" message, not an empty list that looks broken.

## Migration Plan

- New table: `service_requests` (`id`, `customer_id` FK, `customer_location_id` FK, `product_id` FK, `note` nullable, `status` default `pending`, `created_at` default now). Purely additive.
