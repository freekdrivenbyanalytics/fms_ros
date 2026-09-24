# Spec Delta

## ADDED Requirements

### Requirement: Portal-created schedules are eligible for Resco planning
When an assignment is successfully synced for the first time, the system SHALL create a named Active/Planned schedule child (statecode 0, statuscode 1) linked to its Scheduled Work Order and the assigned employee's resource. The booking SHALL preserve the planned start and end as Europe/Oslo wall-clock times using the correct UTC offset. With the corresponding resource, date range and applicable view filters selected, the booking SHALL be visible on Resco's planning screen. Any additional fields required for that visibility SHALL be verified against the live Resco configuration before being mapped. Routine updates SHALL NOT reset a progressed Work Order or schedule to its initial status. Remote failures SHALL retain the existing best-effort local-write behavior and remembered IDs for retry.

#### Scenario: A newly assigned visit appears in Resco planning
- **WHEN** a new assignment successfully syncs and the planner opens the matching resource and date in Resco
- **THEN** its named Planned schedule is visible at the same Oslo-local start and end as the portal assignment

#### Scenario: Rescheduling preserves remote progress
- **WHEN** an existing assignment with a progressed remote schedule or Work Order is synced again
- **THEN** the sync reuses the remembered records without resetting their statuses to Planned or Scheduled

#### Scenario: Booking crosses a seasonal offset change
- **WHEN** a booking is sent for a date in summer or winter time
- **THEN** Resco receives the corresponding Europe/Oslo offset and displays the intended local times

#### Scenario: Remote schedule creation fails
- **WHEN** the Work Order is created but its schedule cannot be created
- **THEN** the local assignment and remembered Work Order ID remain available and retry does not duplicate the Work Order

### Requirement: Existing portal schedules can be repaired without replacing remote records
The system SHALL provide an explicit repair operation scoped to selected existing portal assignments with remembered Work Order and schedule IDs. It SHALL preview proposed changes without writing, and report repaired, skipped and failed items when applied. Only freshly confirmed Active/New schedules belonging to currently Active/Scheduled Work Orders and linked to the selected assignments SHALL be promoted to Planned and receive missing verified planning fields. Repairs SHALL preserve IDs, employee and planned times; SHALL NOT modify manually created orders without portal links; and SHALL reject concurrent remote changes rather than overwrite field progress. Repeating a completed repair SHALL be harmless.

#### Scenario: Existing New schedule is repaired
- **WHEN** an eligible selected assignment's repair is applied
- **THEN** the same schedule becomes named and Planned with verified planning fields, keeping its Work Order, resource and booking times

#### Scenario: Reference order is outside portal ownership
- **WHEN** a manually created Magnus Hognas order has no remembered portal assignment link
- **THEN** repair leaves it untouched

#### Scenario: Remote progress or concurrent change protects a schedule
- **WHEN** either remote record has progressed beyond the repair-eligible states or changes during repair
- **THEN** the item is skipped or reported as a conflict without resetting progress

#### Scenario: Repair is previewed or repeated
- **WHEN** an operator previews a repair or reruns it after success
- **THEN** preview makes no writes and the repeated apply creates no duplicates or additional status transitions

## MODIFIED Requirements

### Requirement: An assignment's Resco Work Order status can be pulled on demand
The system SHALL let a user trigger, on demand only (no automatic or scheduled job), a bulk pull of the current Resco Work Order status for every assignment with a remembered Resco Work Order ID, storing each one's latest status locally. This status-only operation SHALL NOT unassign visits, clear pins, write remote statuses or execute pending Draft-reset retries; those effects belong exclusively to the separately requested overdue-unassignment operation. An assignment with no remembered Resco Work Order ID SHALL be skipped, reported as skipped, and SHALL NOT prevent the pull from continuing to the remaining assignments. A failure pulling one assignment's status SHALL NOT prevent the pull from continuing to the remaining assignments.

#### Scenario: Pulling status updates the locally stored value
- **WHEN** a user triggers a status pull and an assignment has a remembered Resco Work Order ID
- **THEN** the system fetches that Work Order's current status from Resco and stores it against the assignment, replacing whatever was previously stored

#### Scenario: An assignment never synced to Resco is skipped
- **WHEN** a user triggers a status pull and an assignment has no remembered Resco Work Order ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and continues with the remaining assignments

#### Scenario: One assignment's pull failure does not block the rest
- **WHEN** a status pull processes multiple assignments and fetching one fails
- **THEN** the system continues pulling status for the remaining assignments and reports the failure for that one

#### Scenario: The status pull only runs on demand
- **WHEN** the backend starts, or at any other automatic trigger point
- **THEN** no Resco Work Order status pull runs automatically; it only runs when a user explicitly triggers it

#### Scenario: Status sync leaves overdue work and pending resets untouched
- **WHEN** a status-only pull finds past Scheduled assignments or pending Draft resets
- **THEN** it updates cached statuses only, retaining assignments and pending resets without remote writes

