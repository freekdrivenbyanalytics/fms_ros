# Proposal

## Why

Assigned visit cards show Resco IDs but silently omit status until an explicit pull has populated it. Portal-created Work Orders exist as Scheduled in Resco but reportedly do not appear on its planning screen; a live comparison with a manually created Magnus Hognas order found that portal schedule children remain New instead of Planned.

## What Changes

- Always show a labelled Resco Work Order status on assigned cards, including explicit unknown and unsynced states.
- Split All Visits into two actions: "Sync from Resco" only refreshes cached statuses; "Unassign past Scheduled visits" freshly checks eligibility, unassigns qualifying visits and resets their Resco Work Orders to Draft, including durable reset retries.
- Add the same status-only "Sync from Resco" action to Manual Assignment; reserve confirmation and unassignment warnings for the separate unassign action.
- Create named, Planned schedule children with correct employee and Oslo-local booking times, and verify actual Resco planning visibility against the manually created reference.
- Provide a narrowly scoped, repeatable repair for existing portal-linked New schedules, preserving remote progress and identities.
- Investigate preferred windows and owner/view filters before adding any further required payload fields; record the verified minimum mapping.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `assignments`: Explicit status fallback states and on-demand refresh directly on Manual Assignment.
- `resco-integration`: Separate status reads from reconciliation and reset retries; planning-visible schedule creation and safe repair of existing portal-linked schedules.
- `visit-history`: Separate status-sync and unassignment buttons on All Visits.

## Impact

Frontend assigned cards, planning refresh controls and shared status-action presentation; backend Resco schedule payloads and a targeted repair command. Existing status fields can be reused; the backend API must separate status-only sync from explicit reconciliation. No automatic status polling, external-order import, solver change or database migration is expected. Live investigation during proposal used reads only; visual Resco acceptance remains an implementation task.
