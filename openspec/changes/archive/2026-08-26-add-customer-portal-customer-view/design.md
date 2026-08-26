## Context

`CustomerPortalApp.tsx` already holds all six fetched entity lists plus one piece of top-level UI state (`entity`, which of the six views is showing) and renders a persistent sidebar (entity nav) alongside the active view — see `frontend/src/customer-portal/CustomerPortalApp.tsx`. `CustomersView.tsx` currently owns its own local `selected: Customer | null` state (list vs. detail), uncontrolled by the parent, following the same pattern as the other five entity views. `CustomerLocationsView.tsx` is the same shape. See proposal.md - Why / What Changes for motivation and scope; see specs/customer-portal/spec.md (delta) for the required behavior.

## Goals / Non-Goals

**Goals:**
- Make the switcher's selection and the cross-link's target both live as top-level state in `CustomerPortalApp`, since both need to affect which view/detail renders when the user navigates via the sidebar — consistent with how `entity` is already lifted there.
- Keep `CustomersView` and `CustomerLocationsView` the only two components that change; the other four entity views are untouched.

**Non-Goals:**
- No persistence of the switcher's selection across a page reload (resets to "All customers" every load, consistent with the rest of the portal's no-persistence behavior).
- No access control of any kind tied to the switcher — explicitly a display simulation (see proposal.md).

## Decisions

- **Switcher selection lives in `CustomerPortalApp`, rendered inside the existing persistent sidebar.** Add `viewingAsCustomerId: number | null` state (`null` = "All customers") and a `<select>` in the sidebar, above the entity nav buttons — the sidebar already renders unconditionally on every page, so putting the switcher there satisfies "present on every page" for free, with no new persistent-layout component needed. Alternative considered: a separate always-visible top bar spanning both sidebar and content — rejected as an unnecessary extra layout region when the sidebar already serves that role.
- **`CustomersView` gets a `scopedCustomer?: Customer` prop instead of owning list-vs-detail state itself when scoped.** When `viewingAsCustomerId` is set, `CustomerPortalApp` resolves the matching `Customer` and passes it as `scopedCustomer`; `CustomersView` then renders only that customer's detail — no internal list state, no "back to list" control (returning to the full list happens by changing the switcher back to "All customers", not by an action inside the view). When `scopedCustomer` is undefined, `CustomersView` behaves exactly as it does today (its own local list/detail toggle). Alternative considered: keep `CustomersView` fully self-contained and have it read the switcher via context — rejected as unnecessary indirection when `CustomerPortalApp` already threads every other prop down directly.
- **The Customer→Customer Location cross-link uses a one-shot "initial selection" prop, not a router.** `CustomerPortalApp` adds `pendingLocationId: number | null`. Clicking a location link in `CustomersView` calls a handler that sets `entity` to `"customer-locations"` and `pendingLocationId` to that location's id. `CustomerLocationsView` gains an `initialSelectedId?: number` prop, consumed via `useState(() => customerLocations.find(l => l.id === initialSelectedId) ?? null)` — safe because switching `entity` away from `"customer-locations"` unmounts the component, so navigating back through the cross-link always mounts it fresh with the right initial value. Immediately after mount, `CustomerLocationsView` calls an `onInitialSelectionConsumed` callback (in a `useEffect`) so `CustomerPortalApp` clears `pendingLocationId` back to `null` — otherwise, navigating to Customer Locations later via the sidebar's own nav button would incorrectly reopen the same old detail instead of showing the list. Alternative considered: add `react-router` for real per-view URLs/params — rejected per the original Customer Portal design's explicit no-router decision; this one-shot prop is enough for a single cross-link.
- **Customer id display is a plain added column/field**, no new data: `CustomersView`'s list table gets an "ID" column (`customer.id`) and its detail view gets an "ID" `DetailField` — both read the id already present on the existing `Customer` type, no API or type change.

## Risks / Trade-offs

- [A customer with zero Customer Locations gives the cross-link nothing to link to] → Unaffected: the existing "—" empty state for an empty locations list is unchanged; the link only appears per-location, so an empty list simply shows no links, matching current behavior.
- [Lifting `scopedCustomer`/`pendingLocationId` into `CustomerPortalApp` slightly grows its state beyond simple entity-list plumbing] → Acceptable: it's two small, single-purpose fields addressing one cross-view interaction each; still far short of needing a state library or router.
