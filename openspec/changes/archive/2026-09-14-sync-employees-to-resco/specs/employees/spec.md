## MODIFIED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, first name, last name, geographic location (latitude, longitude), an optional email address, an optional mobile phone number, one or more regions they belong to, zero or more products they hold, and a soft-delete flag. An employee's full name SHALL be derived from first name and last name (space-separated) rather than stored as an independently settable value. An employee's working hours are not part of this record; they are resolved per date from that employee's schedule templates and day overrides.

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, first name, last name, latitude, longitude, and at least one region
- **THEN** the system persists the employee and all fields are retrievable unchanged, including its region(s) and products, and its full name is the first and last name joined with a space

#### Scenario: Full name reflects first and last name
- **WHEN** an employee's first name or last name changes
- **THEN** the employee's full name is derived again from the new first and last name, without a separate update to the name itself

### Requirement: Create, update, and soft-delete an employee
The system SHALL allow a user to create an employee with a first name, last name, home location, one or more regions, zero or more products, and optionally an email and mobile phone; update any of those fields; and soft-delete the employee. The system SHALL NOT accept a full name as direct input on create or update. A soft-deleted employee SHALL NOT be permanently removed.

#### Scenario: Creating an employee
- **WHEN** a user creates an employee with a first name, last name, location, and at least one region
- **THEN** the system persists a new employee with those fields and a full name derived from the first and last name

#### Scenario: Updating an employee
- **WHEN** a user updates an employee's first name, last name, location, email, mobile phone, regions, or products
- **THEN** the system persists the change

#### Scenario: Soft-deleting an employee
- **WHEN** a user soft-deletes an employee
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default employee list, while its existing assignments remain unaffected
