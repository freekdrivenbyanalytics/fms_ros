# Tasks

## 1. Confirm planning visibility requirements

- [x] 1.1 Re-read the recorded manual reference and selected portal booking, verify remembered portal ownership and current remote states, and record a minimal comparison of names, status, times, windows, resource and owner in design.md.
- [x] 1.2 Inspect the relevant Resco planning view with controlled resource/date/filter settings, isolate which missing fields prevent visibility, and record the verified minimum payload mapping and before/after evidence in design.md; leave visual acceptance open if UI access is unavailable.

## 2. Make status explicit on Manual Assignment

- [x] 2.1 Render labelled last-known, Not yet refreshed and Not synced states on collapsed and expanded assigned cards; verify all three cases in a browser and preserve complete copyable IDs.
- [x] 2.2 Separate the status-only backend route from a new admin-only reconciliation route; verify mocked tests prove sync cannot delete assignments, clear pins, PATCH Resco or retry pending resets, while explicit reconciliation freshly reads eligibility and retains durable reset retries.
- [x] 2.3 Split All Visits into Sync from Resco and confirmed Unassign past Scheduled visits; share status-only sync with Manual Assignment and update API helpers/types. Verify separate requests/summaries, cancellation, busy states, duplicate prevention and refreshed data on both screens.
- [x] 2.4 Verify opening either screen performs no remote status pull and a failed refresh retains last-known status without inventing a new value; exercise partial and request-level failures with controlled API responses.

## 3. Correct schedule creation and repair existing bookings

- [x] 3.1 Apply the verified schedule mapping, including bounded name and initial Active/Planned state, while preserving parent initialization and update statuses; verify mocked payload tests for creation, rescheduling, progressed statuses, summer/winter offsets and partial-failure retry without duplicate Work Orders.
- [x] 3.2 Add the selected-assignment repair command with dry-run default, explicit apply, identity/resource/time validation, fresh parent/child eligibility checks, conditional writes and per-item results; verify mocked tests for eligible repairs, missing links, progressed states, stale ETags, remote failures, repeated runs and untouched external references.
- [x] 3.3 Preview a selected affected portal booking, apply the eligible repair during implementation, and record returned fields and unchanged IDs/times/resource; verify the manual Magnus reference remains untouched and repeat preview proposes no further changes.

## 4. Verify the complete change

- [x] 4.1 Run relevant backend pytest coverage with remote writes mocked, frontend npm run build and npx oxlint; record results and distinguish existing warnings from introduced issues.
- [x] 4.2 Verify a new portal booking and the repaired existing booking are visible in Resco planning at the correct local times with the expected resource and filters; retain evidence and do not substitute API success for visual acceptance.
- [x] 4.3 Exercise both actions with controlled fixtures: sync retains a past Scheduled assignment and pending reset; explicit unassign re-reads status, preserves future/progressed/failed-read assignments and reconciles only eligible past work. Verify pinned eligibility, retry without an assignment, both screens, confirmation and separate summaries.
- [x] 4.4 Run openspec validate fix-resco-planning-visibility --strict and openspec validate --specs, and reconcile final mappings and any implementation discoveries with design.md and these tasks before archive.
