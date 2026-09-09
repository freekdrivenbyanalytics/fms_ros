## Why

Open-ended contract lines (no `end_date`) currently generate a full year of service visits at creation time. For lines with short intervals this produces enormous row counts — the current database has 97,092 service visits from just 12 contract lines — which is also the direct cause of the Admin Portal's multi-minute load time (see the `speed-up-admin-portal-loading` change). A shorter, rolling horizon keeps that number bounded, but a shorter horizon alone means an open-ended line's visits would simply stop appearing once the window passes, so this change also adds a way to keep extending them.

## What Changes

- Creating a contract line generates visits up to 90 days ahead (down from 365) instead of a full year, for open-ended lines. Bounded lines (with an `end_date`) are unaffected — they already stop at `end_date`.
- A new on-demand "extend visits" operation tops up every open-ended contract line's generated visits back out to 90 days ahead of today, generating only the occurrences between each line's current furthest generated date and the new horizon (idempotent — never duplicates existing visits, and a line already at or beyond the horizon is untouched).
- The Admin Portal's Contracts view gains a button to trigger this extension, following the same on-demand, manual-trigger pattern already used for "Compute driving times" in the Regions view. The same endpoint can also be invoked by an external scheduler (OS-level cron / Task Scheduler) if fully automated top-ups are wanted later — that operational choice is left to the user and isn't part of this change.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `service-visits`: "Creating a contract line generates its service visits" changes its open-ended horizon from 365 days to 90 days; a new requirement adds the on-demand extend-visits operation that tops open-ended lines back out to that horizon.
- `admin-portal`: adds a "extend recurring visits" trigger to the Contracts view, alongside the existing per-entity actions, following the same in-progress/result/error pattern as the Regions view's "Compute driving times" action.

## Impact

- `backend/app/visit_generation.py`: `OPEN_ENDED_HORIZON_DAYS` changes from 365 to 90; gains a function to compute the additional occurrences needed to extend an existing line to a new horizon.
- `backend/app/main.py`: new endpoint to trigger extending all open-ended contract lines' visits.
- `frontend/src/admin-portal/ContractsView.tsx`, `frontend/src/api.ts`: new "extend visits" trigger and result/error display.
- No change to bounded (`end_date` set) contract lines' behavior.
