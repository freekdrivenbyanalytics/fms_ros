## MODIFIED Requirements

### Requirement: Proposed schedule respects hard constraints
The system SHALL only propose scheduling a service visit to an employee when the employee possesses every product the visit's contract requires, the employee is scoped to the visit's region, the employee has a resolved working-hours window for the visit's proposed date and the visit's proposed time window falls entirely within it, and the employee has no time overlap between that proposed visit and any other visit already assigned to them or proposed to them in the same schedule.

#### Scenario: Proposal respects required skills
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** that employee possesses every product the visit's contract requires

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
- **THEN** that employee is not proposed for that visit on that date, even if the employee has the required products, region, and no conflicting visits

### Requirement: Proposed schedule excludes visits without geocoded coordinates
The system SHALL NOT propose scheduling a service visit whose customer location has no resolved geographic coordinates, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit at an ungeocoded location is never scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's customer location has no resolved latitude/longitude
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required products, region, and availability exists

### Requirement: Proposed schedule excludes visits without an assigned region
The system SHALL NOT propose scheduling a service visit whose customer location has no assigned region, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit at a regionless location is never scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's customer location has no assigned region
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required products, coordinates, and availability exists

### Requirement: Proposed schedule excludes visits when no employee has a schedule that day
The system SHALL leave a service visit unscheduled, rather than proposing it, when every employee who otherwise qualifies for it (products, region) has no resolved working-hours window for the visit's proposed date.

#### Scenario: Visit is unscheduled when no qualifying employee has a schedule that day
- **WHEN** a proposed schedule is generated and every employee with the required products and region has no resolved working-hours window for a visit's proposed date
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled

### Requirement: Proposed schedule excludes visits outside the scheduling window
The system SHALL NOT propose scheduling a service visit whose effective schedule date is not today or tomorrow, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit requested further in the future is not scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's effective schedule date is neither today nor tomorrow
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required products, region, and availability exists

#### Scenario: A visit rolls into the window as time passes
- **WHEN** a service visit's effective schedule date, previously beyond tomorrow, becomes today or tomorrow
- **THEN** a subsequently generated proposed schedule considers that visit like any other candidate
