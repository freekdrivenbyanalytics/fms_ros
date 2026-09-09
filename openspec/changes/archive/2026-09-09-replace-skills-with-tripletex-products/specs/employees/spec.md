## MODIFIED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, name, geographic location (latitude, longitude), one or more regions they belong to, zero or more products they hold, and a soft-delete flag. An employee's working hours are not part of this record; they are resolved per date from that employee's schedule templates and day overrides.

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, name, latitude, longitude, and at least one region
- **THEN** the system persists the employee and all fields are retrievable unchanged, including its region(s) and products

### Requirement: List employees
The system SHALL provide an API to retrieve the list of all employees, including each employee's regions and products, excluding employees marked deleted by default.

#### Scenario: Retrieve all employees
- **WHEN** a client requests the list of employees
- **THEN** the system returns all non-deleted persisted employees including their location, regions, and products

#### Scenario: Deleted employee is excluded from the list
- **WHEN** a caller requests the list of employees
- **THEN** employees marked deleted are not included in the result

### Requirement: Create, update, and soft-delete an employee
The system SHALL allow a user to create an employee with a name, home location, one or more regions, and zero or more products; update any of those fields; and soft-delete the employee. A soft-deleted employee SHALL NOT be permanently removed.

#### Scenario: Creating an employee
- **WHEN** a user creates an employee with a name, location, and at least one region
- **THEN** the system persists a new employee with those fields

#### Scenario: Updating an employee
- **WHEN** a user updates an employee's name, location, regions, or products
- **THEN** the system persists the change

#### Scenario: Soft-deleting an employee
- **WHEN** a user soft-deletes an employee
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default employee list, while its existing assignments remain unaffected

## REMOVED Requirements

### Requirement: An employee can have multiple skills
**Reason**: Skills are replaced by Tripletex-sourced products; see "An employee can have multiple products" below.
**Migration**: None needed — the same multi-association shape carries over to products.

## ADDED Requirements

### Requirement: An employee can have multiple products
The system SHALL allow an employee to be associated with more than one product.

#### Scenario: Employee with multiple products
- **WHEN** an employee is associated with two or more products
- **THEN** each association is retrievable and the employee's products include all of them
