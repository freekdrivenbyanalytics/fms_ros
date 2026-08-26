## 1. Customer Switcher

- [x] 1.1 In `CustomerPortalApp.tsx`, add `viewingAsCustomerId: number | null` state (`null` = "All customers") and a `<select>` in the sidebar, above the entity nav, listing "All customers" plus every customer by name.
- [x] 1.2 Resolve `viewingAsCustomerId` to the matching `Customer` (or `undefined`) and pass it to `CustomersView` as a new `scopedCustomer` prop.

## 2. Customers View: Scoped Mode and Id Display

- [x] 2.1 In `CustomersView.tsx`, when `scopedCustomer` is provided, render only that customer's detail (no internal list state, no "back to list" control) instead of the current list/detail toggle.
- [x] 2.2 When `scopedCustomer` is not provided, keep `CustomersView`'s existing list/detail behavior unchanged.
- [x] 2.3 Add an "ID" column to the Customers list table and an "ID" `DetailField` to the customer detail view, both showing the customer's existing `id`.

## 3. Customer → Customer Location Cross-Link

- [x] 3.1 In `CustomerPortalApp.tsx`, add `pendingLocationId: number | null` state and a handler that sets `entity` to `"customer-locations"` and `pendingLocationId` to a given location id.
- [x] 3.2 In `CustomersView.tsx`'s customer detail (both scoped and unscoped), render each listed Customer Location as a clickable link/button that calls the new handler with that location's id.
- [x] 3.3 In `CustomerLocationsView.tsx`, add an `initialSelectedId?: number` prop consumed via lazy `useState` init to open directly at that location's detail; add an `onInitialSelectionConsumed` callback invoked once via `useEffect` on mount so `CustomerPortalApp` can reset `pendingLocationId` to `null`.
- [x] 3.4 Wire `pendingLocationId` and the consumed-callback through `CustomerPortalApp` to `CustomerLocationsView`.

## 4. Verification

- [x] 4.1 Run the frontend dev server and manually verify: the switcher is visible on every entity view (not just Customers); selecting a specific customer shows only that customer's detail when the Customers view is open; the other five views still show all data while a customer is selected; selecting "All customers" restores the full Customers list; the Customers list and a customer's detail both show its id; clicking a Customer Location under a Customer opens that location's own detail view in Customer Locations; navigating to Customer Locations afterward via the sidebar (not via the cross-link) shows the list, not the previously cross-linked detail; and no create/edit/delete control was introduced anywhere.
