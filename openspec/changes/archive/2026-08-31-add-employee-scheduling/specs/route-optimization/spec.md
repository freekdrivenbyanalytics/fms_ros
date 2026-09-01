## MODIFIED Requirements

### Requirement: Proposed schedule respects hard constraints
The system SHALL only propose scheduling a service visit to an employee when the employee possesses every skill the visit's contract requires, the employee is scoped to the visit's region, the employee has a resolved working-hours window for the visit's proposed date and the visit's proposed time window falls entirely within it, and the employee has no time overlap between that proposed visit and any other visit already assigned to them or proposed to them in the same schedule.

#### Scenario: Proposal respects required skills
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** that employee possesses every skill the visit's contract requires

#### Scenario: Proposal respects region
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** that employee is scoped to the visit's region

#### Scenario: Proposal respects working hours
- **WHEN** a proposed schedule assigns a service visit to an employee with a proposed planned start and end time
- **THEN** that time window falls entirely within the employee's working-hours window resolved for that visit's proposed date

#### Scenario: Proposal avoids double-booking
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** the proposed time window does not overlap the time window of any other visit already assigned to that employee, or any other visit proposed to that employee in the same schedule

#### Scenario: Proposal excludes an employee with no resolved schedule for the visit's date
- **WHEN** a proposed schedule is generated and an employee has no resolved working-hours window for a candidate visit's proposed date
- **THEN** that employee is not proposed for that visit on that date, even if the employee has the required skills, region, and no conflicting visits

## ADDED Requirements

### Requirement: Proposed schedule excludes visits when no employee has a schedule that day
The system SHALL leave a service visit unscheduled, rather than proposing it, when every employee who otherwise qualifies for it (skills, region) has no resolved working-hours window for the visit's proposed date.

#### Scenario: Visit is unscheduled when no qualifying employee has a schedule that day
- **WHEN** a proposed schedule is generated and every employee with the required skills and region has no resolved working-hours window for a visit's proposed date
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled
