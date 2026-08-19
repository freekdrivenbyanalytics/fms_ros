## Purpose

Represents the field service employees who can be manually assigned to service visits, including the working hours and home location used to judge assignment feasibility.

## ADDED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, name, work start time, work end time, and geographic location (latitude, longitude).

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, name, work_start, work_end, latitude, and longitude
- **THEN** the system persists the employee and all fields are retrievable unchanged

### Requirement: List employees
The system SHALL provide an API to retrieve the list of all employees.

#### Scenario: Retrieve all employees
- **WHEN** a client requests the list of employees
- **THEN** the system returns all persisted employees including their working hours and location
