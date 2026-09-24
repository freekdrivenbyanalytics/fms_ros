# Spec Delta

## ADDED Requirements

### Requirement: Assigned cards explicitly identify unavailable Resco status
Each assigned visit card SHALL show a labelled Resco Work Order status in its summary and alongside its expanded Resco IDs. A remembered Work Order without a fetched status SHALL show "Not yet refreshed"; an assignment without a remembered Work Order SHALL show "Not synced". A known value SHALL be identified as the last known status. The portal SHALL NOT infer a current Work Order status from the presence of IDs or from the child schedule's status.

#### Scenario: Synced assignment has no cached status
- **WHEN** the card has a Work Order ID but no stored status
- **THEN** it shows "Resco status: Not yet refreshed" instead of omitting status

#### Scenario: Assignment has never synced
- **WHEN** the card has no Work Order ID
- **THEN** it shows "Resco status: Not synced"

#### Scenario: A stored status is available
- **WHEN** a last-known Work Order status is available
- **THEN** the collapsed and expanded card show it as the last-known Resco status and the expanded card retains both complete IDs

### Requirement: Status updates are available from Manual Assignment
Manual Assignment SHALL expose an admin-only "Sync from Resco" action that only fetches and stores current Resco Work Order statuses. It SHALL NOT unassign visits, clear pins, write to Resco or retry pending Draft resets. It SHALL show progress and pulled/skipped/failed results, prevent duplicate submission and reload displayed data afterwards. Opening the screen SHALL NOT trigger a remote pull or reconciliation.

#### Scenario: Planner updates statuses from the board
- **WHEN** the planner selects Sync from Resco on Manual Assignment
- **THEN** statuses refresh without a destructive-action confirmation and all assignments remain assigned, including past Scheduled assignments

#### Scenario: Status update has failures
- **WHEN** a status update reports partial failures or the request fails
- **THEN** the screen displays failures, retains last-known values for failed reads and permits retry

#### Scenario: Planner only opens the board
- **WHEN** the planner opens Manual Assignment without requesting an update
- **THEN** cards use locally stored statuses and fallback states without contacting Resco

## MODIFIED Requirements

### Requirement: Past assignments whose Work Orders are currently Scheduled are automatically unassigned
Only as part of a separately requested on-demand unassignment action, the system SHALL unassign an assignment only when its planned_start date is before today and a successful fresh read confirms its previously synced Work Order is currently Active/Scheduled (statecode 0, statuscode 5). Status-only sync SHALL NOT perform this reconciliation. The explicit unassignment action SHALL fetch fresh statuses independently of any previous sync. It SHALL remove the local assignment, clear its pin, set the visit unassigned and record a reason. This narrow operation SHALL override pin/elapsed-time locks. It SHALL NOT use requested_date or assignment creation time to determine eligibility. It SHALL attempt the corresponding Draft reset specified by resco-integration. Unsynced assignments, failed reads and all other current statuses SHALL be left alone. Audit history and previously observed statuses SHALL NOT determine eligibility; a Work Order that returned to Scheduled is eligible based on its current status.

#### Scenario: An overdue, unsynced assignment is retained
- **WHEN** a past planned assignment has no remembered Work Order ID
- **THEN** reconciliation skips it and leaves it assigned

#### Scenario: A past assignment still Scheduled is unassigned
- **WHEN** the planned work date is before today and a successful read confirms the synced Work Order is currently Scheduled
- **THEN** reconciliation unassigns it locally with a reason, regardless of pin or elapsed-time lock, and attempts a Draft reset

#### Scenario: Another status preserves the assignment
- **WHEN** the Work Order is in any status other than Active/Scheduled
- **THEN** reconciliation leaves the assignment and remote status unchanged

#### Scenario: A failed status read preserves the assignment
- **WHEN** a current status cannot be read successfully
- **THEN** reconciliation reports the failure and does not act on an old cached Scheduled value

#### Scenario: A same-day or future assignment is never auto-unassigned
- **WHEN** planned_start falls today or later, even if requested_date is in the past
- **THEN** reconciliation does not unassign the visit

#### Scenario: The reason clears on reassignment
- **WHEN** an automatically unassigned visit is assigned again manually or through optimization
- **THEN** its unassigned_reason is cleared


#### Scenario: Audit history is unavailable
- **WHEN** a past planned Work Order is currently Scheduled and auditing is unavailable or its previous status was different
- **THEN** reconciliation uses the fresh current status and unassigns it without reading audit history
