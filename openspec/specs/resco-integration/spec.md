# resco-integration Specification

## Purpose

Keeps Resco (the field service mobile CRM technicians log into) aware of fms_ros's employees, by pushing each one to Resco as a User, so a technician added or updated in fms_ros doesn't need to be entered separately in Resco.

## Requirements

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

### Requirement: Customers are synced to Resco as Accounts
The system SHALL let customer data be pushed to Resco by creating or updating a corresponding Account record in Resco, sending that customer's name, email, phone, organization/VAT number, and address.

#### Scenario: A new customer is created as an Account in Resco
- **WHEN** a customer with no remembered Resco Account ID is synced
- **THEN** the system creates a new Account in Resco with that customer's name, email, phone, organization number, and address, and remembers the returned Resco Account ID against that customer

#### Scenario: An existing customer's Account in Resco is updated
- **WHEN** a customer with a remembered Resco Account ID is synced
- **THEN** the system updates that Resco Account's name, email, phone, organization number, and address rather than creating a new one

### Requirement: Customer locations are synced to Resco as Assets
The system SHALL let customer location data be pushed to Resco by creating or updating a corresponding Asset record in Resco, sending that location's address as the Asset's name and linking it to its customer's Resco Account.

#### Scenario: A new customer location is created as an Asset in Resco
- **WHEN** a customer location with no remembered Resco Asset ID is synced, and its customer has a remembered Resco Account ID
- **THEN** the system creates a new Asset in Resco with that location's address as its name, linked to the customer's Resco Account, and remembers the returned Resco Asset ID against that location

#### Scenario: An existing customer location's Asset in Resco is updated
- **WHEN** a customer location with a remembered Resco Asset ID is synced
- **THEN** the system updates that Resco Asset's name rather than creating a new one

#### Scenario: A customer location whose customer isn't yet synced is skipped
- **WHEN** a customer location is synced and its customer has no remembered Resco Account ID
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations — it becomes eligible again once its customer is synced

#### Scenario: A customer location with no street address is skipped
- **WHEN** a customer location with no street address is synced
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations

### Requirement: Customers and customer locations sync to Resco automatically on create and update
The system SHALL attempt to sync a customer to Resco immediately after that customer is created or updated, and a customer location to Resco immediately after that location is created or updated. A failure of this automatic sync (Resco unreachable, an error response, or a missing required dependency) SHALL NOT fail or roll back the customer or customer-location create or update itself.

#### Scenario: Creating a customer triggers a Resco sync attempt
- **WHEN** a user creates a customer
- **THEN** the system attempts to sync that customer to Resco after it is persisted, and the customer is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a customer triggers a Resco sync attempt
- **WHEN** a user updates a customer
- **THEN** the system attempts to sync that customer to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

#### Scenario: Creating a customer location triggers a Resco sync attempt
- **WHEN** a user creates a customer location
- **THEN** the system attempts to sync that location to Resco after it is persisted, and the location is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a customer location triggers a Resco sync attempt
- **WHEN** a user updates a customer location
- **THEN** the system attempts to sync that location to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

### Requirement: A user can manually trigger syncing all customers or all customer locations to Resco
The system SHALL let a user trigger a sync of every non-deleted customer to Resco on demand, and separately a sync of every non-deleted customer location to Resco on demand, each returning a summary of how many were created, updated, skipped, and failed.

#### Scenario: Manually syncing all customers
- **WHEN** a user triggers a manual customer sync to Resco
- **THEN** the system attempts to sync every non-deleted customer to Resco and returns a summary counting how many were created, updated, and failed

#### Scenario: Manually syncing all customer locations
- **WHEN** a user triggers a manual customer location sync to Resco
- **THEN** the system attempts to sync every non-deleted customer location to Resco and returns a summary counting how many were created, updated, skipped (customer not yet synced, or the location has no street address), and failed

### Requirement: Products are synced to Resco
The system SHALL let product data be pushed to Resco by creating or updating a corresponding Product record in Resco, sending that product's name and product number.

#### Scenario: A new product is created in Resco
- **WHEN** a product with no remembered Resco Product ID is synced
- **THEN** the system creates a new Product in Resco with that product's name and number, and remembers the returned Resco Product ID against that product

#### Scenario: An existing product's Resco record is updated
- **WHEN** a product with a remembered Resco Product ID is synced
- **THEN** the system updates that Resco Product's name and number rather than creating a new one

### Requirement: Products sync to Resco on create and update
The system SHALL attempt to sync a product to Resco immediately after that product is created or updated in fms_ros. A failure of this automatic sync SHALL NOT fail or roll back the product create or update itself.

#### Scenario: Creating a product triggers a sync attempt
- **WHEN** a user creates a product in fms_ros
- **THEN** the system attempts to sync that product to Resco after it is persisted, and the product is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a product triggers a sync attempt
- **WHEN** a user updates a product in fms_ros
- **THEN** the system attempts to sync that product to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

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
