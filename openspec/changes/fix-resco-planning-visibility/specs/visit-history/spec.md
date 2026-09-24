# Spec Delta

## MODIFIED Requirements

### Requirement: All-visits page is read-only
The system SHALL NOT offer individual create, edit, assign or unassign controls on All Visits. It SHALL offer two separate admin-only bulk actions: "Sync from Resco" fetches and stores statuses without unassigning or writing to Resco; "Unassign past Scheduled visits" freshly checks current statuses, unassigns eligible past planned assignments and attempts their Resco Draft resets, including retries of pending resets. Only the unassignment action SHALL request confirmation of those consequences, including pinned assignments. Each action SHALL show progress, prevent duplicate submission, report its own results and failures and refresh displayed data. Eligibility SHALL remain current-status-only and SHALL NOT imply verified historical absence of progress.

#### Scenario: No edit affordance on the all-visits page
- **WHEN** a user views a visit on All Visits
- **THEN** no per-visit mutation controls are provided; separate admin bulk sync and unassignment actions are available

#### Scenario: Sync statuses without unassigning
- **WHEN** an admin clicks Sync from Resco
- **THEN** current statuses refresh while all assignments, pins and pending Draft resets remain unchanged and no remote writes occur

#### Scenario: Explicitly unassign eligible past work
- **WHEN** an admin confirms Unassign past Scheduled visits
- **THEN** fresh status reads drive existing past-Scheduled eligibility, local unassignments and conditional Draft resets, and pending resets are retried with their existing protections

#### Scenario: Cancel unassignment
- **WHEN** the admin declines confirmation
- **THEN** no reconciliation or Draft-reset retry is invoked
