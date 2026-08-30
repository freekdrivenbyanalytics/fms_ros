# assignments Specification

## Purpose

Lets a planner manually assign an unassigned service visit to an employee with a chosen planned start time, and view the resulting assignments alongside employees and visits.

## Requirements

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

### Requirement: Unassign an assigned visit
The system SHALL allow a user to remove an assigned service visit's assignment, returning the visit to unassigned status. Unassigning a visit SHALL clear its pin if it was pinned.

#### Scenario: Planner unassigns a visit
- **WHEN** a user unassigns a service visit that currently has an assignment
- **THEN** the system deletes that assignment, sets the visit's status back to unassigned, and the visit no longer appears as pinned

#### Scenario: Unassigning a visit with no assignment is rejected
- **WHEN** a user attempts to unassign a service visit that has no assignment
- **THEN** the system rejects the request and no changes are made

### Requirement: Pin an assigned visit
The system SHALL allow a user to pin or unpin an assigned service visit's assignment. A pinned assignment SHALL be excluded from being changed by the route-optimization capability's schedule runs.

#### Scenario: Planner pins an assignment
- **WHEN** a user pins an assigned service visit's assignment
- **THEN** the system marks that assignment as pinned, and the assignment is shown as pinned to the planner

#### Scenario: Planner unpins an assignment
- **WHEN** a user unpins a previously pinned assignment
- **THEN** the system marks that assignment as no longer pinned

#### Scenario: Pinning is unavailable for a visit with no assignment
- **WHEN** a user attempts to pin a service visit that has no assignment
- **THEN** the system rejects the request

### Requirement: An assignment locks automatically once it has started
The system SHALL treat an assignment as pinned — regardless of its stored pin flag — once its planned start time has passed. This lock is based on elapsed time, not the stored flag, and cannot be removed by unpinning.

#### Scenario: An already-started assignment is shown as pinned
- **WHEN** a user views an assignment whose planned start time has already passed
- **THEN** the system shows that assignment as pinned, even if it was never manually pinned

#### Scenario: Unpinning an already-started assignment does not unlock it
- **WHEN** a user unpins an assignment whose planned start time has already passed
- **THEN** the system updates the stored pin flag, but the assignment continues to be shown as pinned and remains excluded from schedule runs

### Requirement: View employees and visits for assignment
The system SHALL provide a page showing the list of employees, the list of unassigned service visits, and the list of assigned service visits, with each employee card showing its region(s) and skills, and each visit card showing its customer name, region, and required skills, all expandable to show additional detail. Each of the three lists SHALL provide its own independent text search and region/skill filtering, narrowing that list without affecting the other two lists. Each assigned visit card SHALL show whether its assignment is pinned, and offer controls to unassign it and to pin or unpin it.

#### Scenario: Planner views the assignment page
- **WHEN** a user opens the assignment page
- **THEN** the page displays all employees, all unassigned service visits, and all assigned service visits, each employee showing its region(s) and skills, and each visit showing its customer name, region, and required skills

#### Scenario: Planner expands a card for more detail
- **WHEN** a user clicks an employee or service visit card
- **THEN** the card expands to show an info box with additional detail not shown on the collapsed card (at least the region(s) for an employee; at least the address and GPS coordinates for a service visit, whether unassigned or assigned)

#### Scenario: Planner searches a list by name or address
- **WHEN** a user types text into a list's search box
- **THEN** that list shows only the employees or visits whose name (employee name, or visit's customer name) or, for a visit, location address, contains the search text, and the other two lists are unaffected

#### Scenario: Planner filters a list by region and skill
- **WHEN** a user selects one or more regions and/or one or more skills in a list's filters
- **THEN** that list shows only the employees or visits that have at least one of the selected regions (if any region is selected) and at least one of the selected skills (if any skill is selected), and the other two lists are unaffected

#### Scenario: Search and filters combine within a list
- **WHEN** a user has both entered search text and selected region/skill filters on the same list
- **THEN** that list shows only the employees or visits matching the search text and satisfying the selected filters

#### Scenario: No search text and no filters selected
- **WHEN** a list's search box is empty and no region or skill filters are selected
- **THEN** that list shows every employee or visit it would show without search or filtering

#### Scenario: Assigned visit cards show pin state and actions
- **WHEN** a user views the assigned service visits list
- **THEN** each assigned visit card indicates whether it is pinned, and offers an "Unassign" action and a pin/unpin action
