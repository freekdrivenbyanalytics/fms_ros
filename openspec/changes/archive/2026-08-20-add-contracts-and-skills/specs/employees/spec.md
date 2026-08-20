## MODIFIED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, name, work start time, work end time, geographic location (latitude, longitude), one or more regions they belong to, and zero or more skills they hold.

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, name, work_start, work_end, latitude, longitude, and at least one region
- **THEN** the system persists the employee and all fields are retrievable unchanged, including its region(s) and skills

### Requirement: List employees
The system SHALL provide an API to retrieve the list of all employees, including each employee's regions and skills.

#### Scenario: Retrieve all employees
- **WHEN** a client requests the list of employees
- **THEN** the system returns all persisted employees including their working hours, location, regions, and skills

## ADDED Requirements

### Requirement: An employee can have multiple skills
The system SHALL allow an employee to be associated with more than one skill.

#### Scenario: Employee with multiple skills
- **WHEN** an employee is associated with two or more skills
- **THEN** each association is retrievable and the employee's skills include all of them
