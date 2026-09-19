# Spec Delta

## ADDED Requirements

### Requirement: Assignments are synced to Resco as Work Orders
The system SHALL let assignment data be pushed to Resco by creating or updating a corresponding Work Order record in Resco, sending that assignment's planned start and end time, the assigned employee (as the Work Order's resource, via that employee's remembered Resco User ID), and the visit's customer location (as the Work Order's linked asset, via that location's remembered Resco Asset ID).

#### Scenario: A new assignment is created as a Work Order in Resco
- **WHEN** an assignment with no remembered Resco Work Order ID is synced
- **THEN** the system creates a new Work Order in Resco with that assignment's planned start and end time, resource, and linked asset, and remembers the returned Resco Work Order ID against that assignment

#### Scenario: A reassigned assignment's Work Order in Resco is updated
- **WHEN** an assignment with a remembered Resco Work Order ID is synced after its employee or planned time has changed
- **THEN** the system updates that Resco Work Order's resource and/or planned start and end time rather than creating a new one

### Requirement: An assignment whose employee or location isn't yet synced to Resco is skipped, not failed
The system SHALL require the assignment's employee to have a remembered Resco User ID and the visit's customer location to have a remembered Resco Asset ID to sync an assignment to Resco. An assignment missing either SHALL be skipped for that sync, reported as skipped, and SHALL NOT prevent the assignment itself from being created, or other assignments in the same batch from being synced.

#### Scenario: An assignment whose employee isn't yet synced to Resco is skipped
- **WHEN** an assignment is synced whose employee has no remembered Resco User ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and the assignment is still created

#### Scenario: An assignment whose customer location isn't yet synced to Resco is skipped
- **WHEN** an assignment is synced whose visit's customer location has no remembered Resco Asset ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and the assignment is still created

#### Scenario: One assignment's Resco failure does not block others in the same apply
- **WHEN** applying a proposed schedule creates or updates multiple assignments and Resco returns an error for one of them
- **THEN** the system reports that assignment's sync as failed and still attempts every other assignment's sync in the same apply

### Requirement: Assignments sync to Resco automatically when scheduled or rescheduled
The system SHALL attempt to sync an assignment to Resco immediately after it is created or has its employee or planned time changed, whether that happens through manually assigning a visit or through applying a proposed schedule. A failure of this automatic sync (Resco unreachable, an error response, or a missing required dependency) SHALL NOT fail or roll back the assignment create or update itself.

#### Scenario: Manually assigning a visit triggers a sync attempt
- **WHEN** a user manually assigns a visit to an employee
- **THEN** the system attempts to sync that assignment to Resco after it is persisted, and the assignment is persisted regardless of whether that sync attempt succeeds

#### Scenario: Applying a proposed schedule triggers a sync attempt per assignment
- **WHEN** a user applies a proposed schedule
- **THEN** the system attempts to sync each assignment it creates or reassigns to Resco, and the apply's own result is unaffected by whether any of those sync attempts succeed

### Requirement: Unassigning a visit does not affect its Resco Work Order
The system SHALL NOT delete, cancel, or otherwise modify a Resco Work Order as a result of deleting the fms_ros assignment it was created from.

#### Scenario: Deleting an assignment leaves its Work Order untouched in Resco
- **WHEN** a user unassigns a visit that was previously synced to Resco as a Work Order
- **THEN** the system does not call Resco as a result of that deletion
