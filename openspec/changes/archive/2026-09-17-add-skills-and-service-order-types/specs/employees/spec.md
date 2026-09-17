## MODIFIED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, first name, last name, geographic location (latitude, longitude), an optional email address, an optional mobile phone number, one or more regions they belong to, zero or more skills they hold, and a soft-delete flag. An employee's full name SHALL be derived from first name and last name (space-separated) rather than stored as an independently settable value. An employee's working hours are not part of this record; they are resolved per date from that employee's schedule templates and day overrides.

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, first name, last name, latitude, longitude, and at least one region
- **THEN** the system persists the employee and all fields are retrievable unchanged, including its region(s) and skills, and its full name is the first and last name joined with a space

#### Scenario: Full name reflects first and last name
- **WHEN** an employee's first name or last name changes
- **THEN** the employee's full name is derived again from the new first and last name, without a separate update to the name itself

### Requirement: List employees
The system SHALL provide an API to retrieve the list of all employees, including each employee's regions and skills, excluding employees marked deleted by default.

#### Scenario: Retrieve all employees
- **WHEN** a client requests the list of employees
- **THEN** the system returns all non-deleted persisted employees including their location, regions, and skills

#### Scenario: Deleted employee is excluded from the list
- **WHEN** a caller requests the list of employees
- **THEN** employees marked deleted are not included in the result

### Requirement: Create, update, and soft-delete an employee
The system SHALL allow a user to create an employee with a first name, last name, home location, one or more regions, zero or more skills, and optionally an email and mobile phone; update any of those fields; and soft-delete the employee. The system SHALL NOT accept a full name as direct input on create or update. A soft-deleted employee SHALL NOT be permanently removed.

#### Scenario: Creating an employee
- **WHEN** a user creates an employee with a first name, last name, location, and at least one region
- **THEN** the system persists a new employee with those fields and a full name derived from the first and last name

#### Scenario: Updating an employee
- **WHEN** a user updates an employee's first name, last name, location, email, mobile phone, regions, or skills
- **THEN** the system persists the change

#### Scenario: Soft-deleting an employee
- **WHEN** a user soft-deletes an employee
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default employee list, while its existing assignments remain unaffected

## REMOVED Requirements

### Requirement: An employee can have multiple products
**Reason**: Employee qualification is now expressed as skills the employee holds, not products — see the new "An employee can have multiple skills" requirement. A product's role is now to declare what skills it requires (see the `products` capability), and an employee's qualification for a product is derived by comparing the employee's skills against the product's required skills, rather than the employee holding the product directly.
**Migration**: No data migration needed for `employee_products` — that association is dropped outright (per this change's design), and each active employee is instead assigned skills directly as part of this change's demo-data task.

## ADDED Requirements

### Requirement: An employee can have multiple skills
The system SHALL allow an employee to be associated with more than one skill.

#### Scenario: Employee with multiple skills
- **WHEN** an employee is associated with two or more skills
- **THEN** each association is retrievable and the employee's skills include all of them
