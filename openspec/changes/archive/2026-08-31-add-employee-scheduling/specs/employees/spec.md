## MODIFIED Requirements

### Requirement: Employee data model
The system SHALL persist each employee with a unique identifier, name, geographic location (latitude, longitude), one or more regions they belong to, zero or more skills they hold, and a soft-delete flag. An employee's working hours are not part of this record; they are resolved per date from that employee's schedule templates and day overrides.

#### Scenario: Employee is persisted with required fields
- **WHEN** an employee record is created with id, name, latitude, longitude, and at least one region
- **THEN** the system persists the employee and all fields are retrievable unchanged, including its region(s) and skills

### Requirement: List employees
The system SHALL provide an API to retrieve the list of all employees, including each employee's regions and skills, excluding employees marked deleted by default.

#### Scenario: Retrieve all employees
- **WHEN** a client requests the list of employees
- **THEN** the system returns all non-deleted persisted employees including their location, regions, and skills

#### Scenario: Deleted employee is excluded from the list
- **WHEN** a caller requests the list of employees
- **THEN** employees marked deleted are not included in the result

### Requirement: An employee can belong to multiple regions
The system SHALL allow an employee to be associated with more than one region.

#### Scenario: Employee with multiple regions
- **WHEN** an employee is associated with two or more regions
- **THEN** each association is retrievable and the employee's regions include all of them

### Requirement: An employee can have multiple skills
The system SHALL allow an employee to be associated with more than one skill.

#### Scenario: Employee with multiple skills
- **WHEN** an employee is associated with two or more skills
- **THEN** each association is retrievable and the employee's skills include all of them

## ADDED Requirements

### Requirement: Create, update, and soft-delete an employee
The system SHALL allow a user to create an employee with a name, home location, one or more regions, and zero or more skills; update any of those fields; and soft-delete the employee. A soft-deleted employee SHALL NOT be permanently removed.

#### Scenario: Creating an employee
- **WHEN** a user creates an employee with a name, location, and at least one region
- **THEN** the system persists a new employee with those fields

#### Scenario: Updating an employee
- **WHEN** a user updates an employee's name, location, regions, or skills
- **THEN** the system persists the change

#### Scenario: Soft-deleting an employee
- **WHEN** a user soft-deletes an employee
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default employee list, while its existing assignments remain unaffected

### Requirement: Employee schedule template data model
The system SHALL persist each employee schedule template with a unique identifier, the employee it belongs to, a start date, an end date, a work start time, a work end time, a maximum hours per day, a lunch type (none, fixed, or flexible), an optional lunch start time, an optional lunch end time, an optional lunch duration, and a soft-delete flag.

#### Scenario: Schedule template is persisted with required fields
- **WHEN** a schedule template is created with id, employee_id, start_date, end_date, work_start, work_end, max_hours_per_day, and lunch_type
- **THEN** the system persists the template and all fields are retrievable unchanged

### Requirement: An employee's schedule templates cannot overlap
The system SHALL reject creating or updating a schedule template whose date range overlaps another non-deleted template belonging to the same employee.

#### Scenario: Overlapping template is rejected
- **WHEN** a user creates a schedule template for an employee whose date range overlaps one of that employee's existing non-deleted templates
- **THEN** the system rejects the request and does not persist the new template

#### Scenario: Non-overlapping template is accepted
- **WHEN** a user creates a schedule template for an employee whose date range does not overlap any of that employee's existing non-deleted templates
- **THEN** the system persists the new template

### Requirement: Create, update, and soft-delete an employee schedule template
The system SHALL allow a user to create a schedule template for an employee covering a date range, update its date range, hours, max-hours-per-day cap, or lunch fields, and soft-delete it. A soft-deleted template SHALL NOT be permanently removed.

#### Scenario: Creating a schedule template
- **WHEN** a user creates a schedule template for an employee with a date range, work hours, and a max hours per day
- **THEN** the system persists a new template linked to that employee

#### Scenario: Updating a schedule template
- **WHEN** a user updates a schedule template's date range, hours, max hours per day, or lunch fields
- **THEN** the system persists the change

#### Scenario: Soft-deleting a schedule template
- **WHEN** a user soft-deletes a schedule template
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default template list, and it is no longer used to resolve any employee's schedule

### Requirement: Employee schedule day override data model
The system SHALL persist each employee schedule day override with a unique identifier, the employee it belongs to, a specific date, a day type (working, holiday, or sick), an optional work start time, an optional work end time, an optional maximum hours per day, an optional overtime duration in minutes, and a soft-delete flag. A holiday or sick override SHALL NOT carry work hours or overtime. At most one non-deleted override SHALL exist per employee per date.

#### Scenario: Working-day override is persisted with hours
- **WHEN** a day override is created with day_type "working", a work_start, and a work_end for a given employee and date
- **THEN** the system persists the override and all fields are retrievable unchanged

#### Scenario: Holiday or sick override is persisted without hours
- **WHEN** a day override is created with day_type "holiday" or "sick" for a given employee and date
- **THEN** the system persists the override with no work hours

#### Scenario: A second override for the same employee and date is rejected
- **WHEN** a user creates a day override for an employee and date that already has a non-deleted override
- **THEN** the system rejects the request and does not persist the new override

### Requirement: Create, update, and soft-delete an employee schedule day override
The system SHALL allow a user to create a day override for an employee and date, update its day type, hours, max-hours-per-day cap, or overtime minutes, and soft-delete it. A soft-deleted override SHALL NOT be permanently removed.

#### Scenario: Creating a day override
- **WHEN** a user creates a day override for an employee and a specific date
- **THEN** the system persists a new override linked to that employee and date

#### Scenario: Updating a day override
- **WHEN** a user updates a day override's day type, hours, max hours per day, or overtime minutes
- **THEN** the system persists the change

#### Scenario: Recording overtime on a working day override
- **WHEN** a user sets an overtime duration on a working-type day override
- **THEN** the system persists the overtime duration alongside that override's regular hours

#### Scenario: Soft-deleting a day override
- **WHEN** a user soft-deletes a day override
- **THEN** the system marks it deleted rather than removing it, and it is no longer used to resolve that employee's schedule for that date

### Requirement: A day's effective hours cannot exceed its effective max hours per day
The system SHALL reject a working day (a working-type override with its own hours, or a template-covered day) whose work end minus work start exceeds the effective max hours per day for that day: the override's own max-hours-per-day if it specifies one, otherwise the covering template's max-hours-per-day.

#### Scenario: A working override exceeding its own cap is rejected
- **WHEN** a user creates or updates a working-type day override whose work_end minus work_start exceeds the max_hours_per_day given on that same override
- **THEN** the system rejects the request

#### Scenario: A template whose hours exceed its own cap is rejected
- **WHEN** a user creates or updates a schedule template whose work_end minus work_start exceeds its own max_hours_per_day
- **THEN** the system rejects the request

#### Scenario: A working override without its own cap is checked against the covering template's cap
- **WHEN** a user creates a working-type day override with hours but no max_hours_per_day, for a date covered by an existing template
- **THEN** the system rejects the request if the override's hours exceed that template's max_hours_per_day, and accepts it otherwise

### Requirement: An employee's effective schedule for a date is resolved from overrides and templates
The system SHALL resolve an employee's effective working-hours window for a given date as follows: if a non-deleted day override exists for that employee and date, use it — a "working" override's own regular hours if it has them, otherwise the covering template's hours; a "holiday" or "sick" override means the employee has no working-hours window that date. If no override exists, use the non-deleted template whose date range covers that date, if any. If neither an override nor a covering template exists, the employee has no working-hours window that date. A working override's overtime duration is never part of the resolved working-hours window.

#### Scenario: Override with its own hours takes precedence
- **WHEN** an employee has both a covering template and a working-type day override with its own hours for the same date
- **THEN** the resolved working-hours window for that date is the override's hours

#### Scenario: Working override without its own hours falls back to the template
- **WHEN** an employee has a working-type day override with no hours of its own, for a date covered by a template
- **THEN** the resolved working-hours window for that date is the template's hours

#### Scenario: Holiday or sick override means no working hours
- **WHEN** an employee has a holiday or sick day override for a date
- **THEN** the employee has no resolved working-hours window for that date, even if a template also covers it

#### Scenario: No override falls back to the covering template
- **WHEN** an employee has no day override for a date but has a template whose date range covers it
- **THEN** the resolved working-hours window for that date is the template's hours

#### Scenario: No override and no covering template means no working hours
- **WHEN** an employee has neither a day override nor a template covering a date
- **THEN** the employee has no resolved working-hours window for that date

#### Scenario: Overtime is excluded from the resolved window
- **WHEN** an employee has a working-type day override with an overtime duration for a date
- **THEN** the resolved working-hours window for that date reflects only the override's regular hours, not the overtime duration

### Requirement: Overtime is recorded but not yet used for scheduling
The system SHALL persist a day override's overtime duration and make it retrievable, but SHALL NOT use it when resolving an employee's working-hours window, when validating a day's hours against its effective max-hours-per-day cap, or when the route optimizer proposes a schedule. Using overtime to influence scheduling or prioritization is deferred to a later change.

#### Scenario: Overtime does not extend the schedulable window
- **WHEN** an employee's day override for a date has an overtime duration
- **THEN** that date's resolved working-hours window, and any schedule the route optimizer proposes for that date, are unaffected by the overtime duration

#### Scenario: Overtime is not checked against the max-hours-per-day cap
- **WHEN** a user sets an overtime duration on a day override, such that regular hours plus overtime would exceed the effective max hours per day
- **THEN** the system does not reject the override on that basis

### Requirement: Deleted schedule templates and day overrides are hidden by default
The system SHALL exclude schedule templates and day overrides marked deleted from the lists returned to callers by default, and SHALL NOT use them when resolving an employee's effective schedule.

#### Scenario: Deleted template is excluded from the list
- **WHEN** a caller requests an employee's schedule templates
- **THEN** templates marked deleted are not included in the result

#### Scenario: Deleted override is excluded from the list
- **WHEN** a caller requests an employee's day overrides
- **THEN** overrides marked deleted are not included in the result
