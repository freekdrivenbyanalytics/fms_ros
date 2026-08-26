## Why

The Customer Portal (see `openspec/specs/customer-portal/spec.md`) currently shows every customer's data to whoever opens it — there is no way to preview what a specific customer would see if they were the one logged in. Adding a lightweight, no-auth "viewing as" customer switcher, along with an id and clickable cross-navigation on the Customer view, moves the portal a step closer to the eventual customer self-service experience while still deferring real authentication.

## What Changes

- Add a customer switcher control, present on every page of the Customer Portal (in the same shared sidebar used for entity navigation), letting the user pick "All customers" (default) or one specific customer to "view as."
- When a specific customer is selected, opening the Customers entity no longer shows the list of all customers — it goes straight to that one customer's own detail page instead. The other five entity views (Employees, Customer Locations, Contracts, Skills, Regions) are unaffected and continue showing all data regardless of the switcher's selection.
- Selecting "All customers" again restores the full Customers list view.
- Display each customer's existing database id (e.g. "Customer #3") on the Customers list and on a customer's detail view. This is a display-only addition — no new field, no backend or data model change.
- On a Customer's detail view, each of its listed Customer Locations becomes a clickable link that opens that location's own detail view (within Customer Locations). No other relationship reference in the portal changes.
- Explicitly no authentication or authorization: the switcher is a client-side display simulation only. Selecting a customer does not restrict what data is fetched or what any other view shows — anyone can still switch to any customer or browse everything unfiltered. A real login/role system remains a separate future change.

## Capabilities

### Modified Capabilities
- `customer-portal`: Adds the customer switcher and its effect on the Customers view, adds id display on Customers, and adds clickable navigation from a Customer's Customer Locations to their own detail view.

## Impact

- **Affected code**: `frontend/src/customer-portal/CustomerPortalApp.tsx` (switcher state, passed down to `CustomersView`), `frontend/src/customer-portal/CustomersView.tsx` (id display, skip-list-when-scoped behavior, clickable location links), `frontend/src/customer-portal/CustomerLocationsView.tsx` (support being opened directly at a specific location, for the new cross-link). No backend changes, no new dependencies.
- **Affected systems**: Frontend only, within the existing Customer Portal area.
- **Dependencies**: None planned.
