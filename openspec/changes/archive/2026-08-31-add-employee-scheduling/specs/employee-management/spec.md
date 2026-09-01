## Purpose

Gives a planner a dedicated, standalone area to manage employee masterdata and each employee's working-hours schedule — templates, day-by-day overrides, holidays, and sickness — kept clearly separate from both the Planning application and the Customer Portal.

## ADDED Requirements

### Requirement: Employee Management is a separate top-level area
The system SHALL provide Employee Management as a top-level area reachable via a landing entry point distinct from both the Planning application's navigation and the Customer Portal, sharing no header or navigation elements with either.

#### Scenario: User reaches Employee Management
- **WHEN** a user navigates to the Employee Management entry point
- **THEN** the system shows Employee Management without any Planning-application or Customer Portal navigation visible alongside it

#### Scenario: Employee Management and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves Employee Management
- **THEN** any employee visible in the Planning application is also visible in Employee Management, and vice versa

### Requirement: Employee list and detail views
The system SHALL provide, within Employee Management, a list view of all non-deleted employees and a detail view for each employee showing its own fields, the regions it is scoped to, the skills it holds, its schedule templates, and its day overrides.

#### Scenario: User browses the employee list
- **WHEN** a user opens the employee list view in Employee Management
- **THEN** the system shows every non-deleted employee currently in the database

#### Scenario: User opens an employee's detail view
- **WHEN** a user opens an employee's detail view in Employee Management
- **THEN** the system shows that employee's own fields, its regions, its skills, its schedule templates, and its day overrides

### Requirement: Create, update, and soft-delete an employee from Employee Management
The system SHALL let a user create an employee (name, home location, regions, skills), update any of those fields, and soft-delete the employee, from Employee Management.

#### Scenario: Creating an employee in Employee Management
- **WHEN** a user creates an employee from Employee Management
- **THEN** the system persists the new employee and it appears in the employee list

#### Scenario: Updating an employee in Employee Management
- **WHEN** a user updates an employee's fields from Employee Management
- **THEN** the system persists the change

#### Scenario: Soft-deleting an employee in Employee Management
- **WHEN** a user soft-deletes an employee from Employee Management
- **THEN** the system marks it deleted and it no longer appears in the employee list

### Requirement: Apply a schedule template for a date range from Employee Management
The system SHALL let a user, from an employee's detail view, create a schedule template by specifying a date range, work start and end times, a maximum hours per day, and lunch fields, update an existing template's fields, and soft-delete it.

#### Scenario: Applying a template for a period
- **WHEN** a user creates a schedule template for an employee with a start date, end date, and work hours (for example 08:00–16:00 from 2026-01-01 to 2026-12-31)
- **THEN** the system persists the template and it governs that employee's resolved schedule for every date in that range not covered by a day override

#### Scenario: Updating a template
- **WHEN** a user updates a schedule template's date range, hours, max hours per day, or lunch fields from Employee Management
- **THEN** the system persists the change

#### Scenario: Soft-deleting a template
- **WHEN** a user soft-deletes a schedule template from Employee Management
- **THEN** the system marks it deleted and it no longer appears in the employee's list of templates

### Requirement: Adjust a single day's schedule from Employee Management
The system SHALL let a user, from an employee's detail view, create a day override for a specific date with its own work start and end time (for example changing one day within a templated period to 09:00–17:00), update it, and soft-delete it.

#### Scenario: Overriding a single day's hours
- **WHEN** a user creates a working-type day override for an employee and a specific date with its own hours
- **THEN** the system persists the override and it governs that employee's resolved schedule for that date instead of any covering template

#### Scenario: Updating a day override
- **WHEN** a user updates a day override's hours or max hours per day from Employee Management
- **THEN** the system persists the change

#### Scenario: Soft-deleting a day override
- **WHEN** a user soft-deletes a day override from Employee Management
- **THEN** the system marks it deleted and it no longer appears in the employee's list of overrides

### Requirement: Record overtime for a day from Employee Management
The system SHALL let a user record an overtime duration on a working-type day override from an employee's detail view. The system SHALL indicate that overtime is not currently used by the route optimizer.

#### Scenario: Recording overtime for a day
- **WHEN** a user sets an overtime duration on a working-type day override from Employee Management
- **THEN** the system persists the overtime duration on that override

#### Scenario: Overtime is labeled as not yet solver-visible
- **WHEN** a user views the overtime field on a day override in Employee Management
- **THEN** the system indicates that this value is not currently taken into account when proposing a schedule

### Requirement: Quickly mark holidays and sickness from Employee Management
The system SHALL let a user mark one date, or a range of dates, as "holiday" or "sick" for an employee in a single action, creating one day override per date in the range.

#### Scenario: Marking a single day as holiday
- **WHEN** a user marks one date as holiday for an employee
- **THEN** the system creates a day override for that date with day_type "holiday" and no work hours

#### Scenario: Marking a range of days as sick
- **WHEN** a user marks a range of dates as sick for an employee
- **THEN** the system creates one day override per date in that range, each with day_type "sick" and no work hours

### Requirement: Employee Management surfaces schedule validation errors
The system SHALL show a user-facing error, without persisting the change, when a requested template or day override would overlap another template, duplicate an existing override for the same date, or exceed the effective max hours per day.

#### Scenario: Overlapping template is rejected with an explanation
- **WHEN** a user attempts to create a schedule template whose date range overlaps an existing one for the same employee
- **THEN** Employee Management shows an error and does not create the template

#### Scenario: Over-cap hours are rejected with an explanation
- **WHEN** a user attempts to create or update a template or day override whose hours exceed its effective max hours per day
- **THEN** Employee Management shows an error and does not persist the change
