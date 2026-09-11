## ADDED Requirements

### Requirement: View each employee's driving route for the selected day on a map
The system SHALL display, alongside the day planning timeline chart, a map showing every employee with at least one assignment on the selected day, with that employee's route for the day drawn as a road-following path from their home location through their assignments' customer locations in planned-start order.

#### Scenario: Employee with assignments shows a route
- **WHEN** the day planning page is showing a day on which an employee has one or more assignments
- **THEN** the map draws that employee's route starting at their home location and passing through each of that day's assignment locations in ascending order of planned_start, using a road-following path rather than a straight line between stops

#### Scenario: Employee with no assignments that day has no route
- **WHEN** the day planning page is showing a day on which an employee has no assignments
- **THEN** the map draws no route for that employee

#### Scenario: Route updates when the selected day changes
- **WHEN** a user changes the day planning page's selected day
- **THEN** the map's routes are recomputed and redrawn for the newly selected day

### Requirement: Distinguish each employee's route on the map
The system SHALL render each employee's route in a visually distinct color from every other employee's route shown on the same map, and SHALL mark each stop (home and each visit location) along a route.

#### Scenario: Two employees' routes are visually distinguishable
- **WHEN** the map shows routes for two or more employees on the same day
- **THEN** each employee's route is rendered in a different color from the others

### Requirement: View visit detail from a route marker
The system SHALL let a user view a visit's customer name and planned start/end time by interacting with that visit's marker on the day planning map, and view an employee's name by interacting with their route or home marker.

#### Scenario: Planner inspects a visit marker
- **WHEN** a user interacts with a visit marker on the day planning map
- **THEN** the system shows that visit's customer name and planned start and end time

#### Scenario: Planner inspects a route
- **WHEN** a user interacts with an employee's route or home marker on the day planning map
- **THEN** the system shows that employee's name
