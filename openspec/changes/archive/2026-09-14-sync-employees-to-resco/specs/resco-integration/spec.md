## Purpose

Keeps Resco (the field service mobile CRM technicians log into) aware of fms_ros's employees, by pushing each one to Resco as a User, so a technician added or updated in fms_ros doesn't need to be entered separately in Resco.

## ADDED Requirements

### Requirement: Employees are synced to Resco as Users
The system SHALL let employee data be pushed to Resco by creating or updating a corresponding User record in Resco, sending that employee's first name, last name, email, and mobile phone.

#### Scenario: A new employee is created as a User in Resco
- **WHEN** an employee with no remembered Resco User ID is synced
- **THEN** the system creates a new User in Resco with that employee's first name, last name, email, and mobile phone, and remembers the returned Resco User ID against that employee

#### Scenario: An existing employee's User in Resco is updated
- **WHEN** an employee with a remembered Resco User ID is synced
- **THEN** the system updates that Resco User's first name, last name, email, and mobile phone rather than creating a new one

### Requirement: An employee missing a field Resco requires is skipped, not failed
The system SHALL require an email and a mobile phone number to sync an employee to Resco. An employee missing either SHALL be skipped for that sync, reported as skipped, and SHALL NOT prevent other employees in the same sync from being processed.

#### Scenario: An employee missing email or mobile phone is skipped
- **WHEN** a sync processes an employee with no email, no mobile phone, or neither
- **THEN** the system does not call Resco for that employee, reports it as skipped, and continues processing the remaining employees

#### Scenario: One employee's Resco failure does not block others
- **WHEN** a sync processes multiple employees and Resco returns an error for one of them
- **THEN** the system reports that employee as failed and still attempts every other employee in the sync

### Requirement: Employees sync to Resco automatically on create and update
The system SHALL attempt to sync an employee to Resco immediately after that employee is created or updated. A failure of this automatic sync (Resco unreachable, an error response, or a missing required field) SHALL NOT fail or roll back the employee create or update itself.

#### Scenario: Creating an employee triggers a sync attempt
- **WHEN** a user creates an employee
- **THEN** the system attempts to sync that employee to Resco after the employee is persisted, and the employee is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating an employee triggers a sync attempt
- **WHEN** a user updates an employee
- **THEN** the system attempts to sync that employee to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

### Requirement: A user can manually trigger syncing all employees
The system SHALL let a user trigger a sync of every non-deleted employee to Resco on demand, returning a summary of how many were created, updated, skipped, and failed.

#### Scenario: Manually syncing all employees
- **WHEN** a user triggers a manual sync
- **THEN** the system attempts to sync every non-deleted employee to Resco and returns a summary counting how many were created, updated, skipped (missing required fields), and failed (a Resco error)
