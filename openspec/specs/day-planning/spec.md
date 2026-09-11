# day-planning Specification

## Purpose

Gives a planner a read-only, at-a-glance view of how a single day's work is laid out across employees, without needing to piece the schedule together from individual assignment records.

## Requirements

### Requirement: View all employees on a single combined timeline chart
The system SHALL display a single combined timeline chart for the selected day, containing one row per employee within that one chart (not a separate chart per employee), with a timeline block for each of that employee's assignments on that day, positioned according to the assignment's planned_start and planned_end and labeled with the visit's customer name.

#### Scenario: Planner opens the day planning page
- **WHEN** a user opens the day planning page
- **THEN** the page renders one single timeline chart containing a row for every employee, and each employee's row shows a timeline block for every assignment whose planned_start falls on the selected day, positioned between the assignment's planned_start and planned_end and labeled with the assignment's visit's customer name

#### Scenario: Employee with no assignments on the selected day
- **WHEN** an employee has no assignment whose planned_start falls on the selected day
- **THEN** that employee's row is shown within the same combined chart with no timeline blocks

### Requirement: View full assignment detail from a timeline block
The system SHALL let a user view an assignment's full service visit detail — the customer, address, region, and required products — from its timeline block on the day planning chart.

#### Scenario: Planner expands a timeline block
- **WHEN** a user expands a timeline block
- **THEN** the system shows the visit's customer name, address, region, and required products, alongside the assignment's planned start and end times

### Requirement: View employee products on the chart
The system SHALL show, on each employee's row label in the day planning chart, the products that employee possesses.

#### Scenario: Planner views an employee's row
- **WHEN** the day planning chart renders an employee's row
- **THEN** the row label shows the employee's name and the products that employee possesses

### Requirement: Select which day to view
The system SHALL let a user choose which day's schedule the day planning page displays, defaulting to the current day, and SHALL let the user move to the previous or next day.

#### Scenario: Page defaults to today
- **WHEN** a user opens the day planning page without having chosen a day
- **THEN** the page displays assignments for the current day

#### Scenario: Planner navigates to a different day
- **WHEN** a user selects a different date, or uses the previous/next day control
- **THEN** the page updates to show only assignments whose planned_start falls on the newly selected day

### Requirement: Day planning view is read-only
The system SHALL NOT allow creating, editing, or deleting an assignment from the day planning page.

#### Scenario: No edit affordance on a timeline block
- **WHEN** a user views or interacts with a timeline block on the day planning page
- **THEN** the system provides no action to create, edit, or delete the underlying assignment from that page

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
