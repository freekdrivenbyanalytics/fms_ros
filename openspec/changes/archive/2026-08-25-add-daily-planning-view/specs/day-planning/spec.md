## Purpose

Gives a planner a read-only, at-a-glance view of how a single day's work is laid out across employees, without needing to piece the schedule together from individual assignment records.

## ADDED Requirements

### Requirement: View all employees on a single combined timeline chart
The system SHALL display a single combined timeline chart for the selected day, containing one row per employee within that one chart (not a separate chart per employee), with a timeline block for each of that employee's assignments on that day, positioned according to the assignment's planned_start and planned_end and labeled with the visit's customer name.

#### Scenario: Planner opens the day planning page
- **WHEN** a user opens the day planning page
- **THEN** the page renders one single timeline chart containing a row for every employee, and each employee's row shows a timeline block for every assignment whose planned_start falls on the selected day, positioned between the assignment's planned_start and planned_end and labeled with the assignment's visit's customer name

#### Scenario: Employee with no assignments on the selected day
- **WHEN** an employee has no assignment whose planned_start falls on the selected day
- **THEN** that employee's row is shown within the same combined chart with no timeline blocks

### Requirement: View full assignment detail from a timeline block
The system SHALL let a user view an assignment's full service visit detail — the customer, address, region, and required skills — from its timeline block on the day planning chart.

#### Scenario: Planner expands a timeline block
- **WHEN** a user expands a timeline block
- **THEN** the system shows the visit's customer name, address, region, and required skills, alongside the assignment's planned start and end times

### Requirement: View employee skills on the chart
The system SHALL show, on each employee's row label in the day planning chart, the skills that employee possesses.

#### Scenario: Planner views an employee's row
- **WHEN** the day planning chart renders an employee's row
- **THEN** the row label shows the employee's name and the skills that employee possesses

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
