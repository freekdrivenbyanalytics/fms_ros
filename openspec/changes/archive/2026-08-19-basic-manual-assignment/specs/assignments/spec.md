## Purpose

Lets a planner manually assign an unassigned service visit to an employee with a chosen planned start time, and view the resulting assignments alongside employees and visits.

## ADDED Requirements

### Requirement: Assignment data model
The system SHALL persist each assignment with the service visit it applies to, the employee it is assigned to, a planned start time, and a planned end time.

#### Scenario: Assignment is persisted with required fields
- **WHEN** an assignment is created linking a service visit to an employee with a planned start time
- **THEN** the system persists the assignment with the service_visit_id, employee_id, planned_start, and planned_end

### Requirement: Manually assign an unassigned visit
The system SHALL allow a user to manually assign an unassigned service visit to an employee by selecting a planned start time.

#### Scenario: Successful manual assignment
- **WHEN** a user assigns an unassigned service visit to an employee and selects a planned start time
- **THEN** the system creates an assignment for that visit and employee, sets planned_start to the selected time, computes planned_end as planned_start plus the visit's duration_minutes, and updates the visit's status to `assigned`

### Requirement: Prevent double assignment
The system SHALL reject a request to assign a service visit whose status is already `assigned`.

#### Scenario: Assigning an already-assigned visit is rejected
- **WHEN** a user attempts to assign a service visit whose status is already `assigned`
- **THEN** the system rejects the request and the visit's existing assignment remains unchanged

### Requirement: View employees and visits for assignment
The system SHALL provide a page showing the list of employees, the list of unassigned service visits, and the list of assigned service visits.

#### Scenario: Planner views the assignment page
- **WHEN** a user opens the assignment page
- **THEN** the page displays all employees, all unassigned service visits, and all assigned service visits
