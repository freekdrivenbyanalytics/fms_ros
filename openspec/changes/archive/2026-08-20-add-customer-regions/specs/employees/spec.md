## MODIFIED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, name, work start time, work end time, geographic location (latitude, longitude), and one or more regions they belong to.

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, name, work_start, work_end, latitude, longitude, and at least one region
- **THEN** the system persists the employee and all fields are retrievable unchanged, including its region(s)

### Requirement: List employees
The system SHALL provide an API to retrieve the list of all employees, including each employee's regions.

#### Scenario: Retrieve all employees
- **WHEN** a client requests the list of employees
- **THEN** the system returns all persisted employees including their working hours, location, and regions

## ADDED Requirements

### Requirement: An employee can belong to multiple regions
The system SHALL allow an employee to be associated with more than one region.

#### Scenario: Employee with multiple regions
- **WHEN** an employee is associated with two or more regions
- **THEN** each association is retrievable and the employee's regions include all of them
