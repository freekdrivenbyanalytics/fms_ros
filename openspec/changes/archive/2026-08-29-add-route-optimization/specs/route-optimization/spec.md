## Purpose

Proposes an optimized employee/visit schedule for every currently unassigned service visit, respecting each employee's skills, region, working hours, and existing commitments, and minimizing travel between an employee's visits — for a planner to review and apply as real assignments.

## ADDED Requirements

### Requirement: Generate a proposed schedule
The system SHALL let a user request a proposed schedule covering every currently unassigned service visit, computed from the current employees, unassigned service visits, and existing assignments, without creating any assignment as a result of generating the proposal.

#### Scenario: Planner requests a proposed schedule
- **WHEN** a user requests a proposed schedule
- **THEN** the system returns a proposal that, for each currently unassigned service visit, either names the employee and planned start/end time it proposes for that visit, or leaves it unscheduled if no feasible assignment exists, and no assignment is created as a result

### Requirement: Proposed schedule respects hard constraints
The system SHALL only propose scheduling a service visit to an employee when the employee possesses every skill the visit's contract requires, the employee is scoped to the visit's region, the visit's proposed time window falls entirely within the employee's working hours, and the employee has no time overlap between that proposed visit and any other visit already assigned to them or proposed to them in the same schedule.

#### Scenario: Proposal respects required skills
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** that employee possesses every skill the visit's contract requires

#### Scenario: Proposal respects region
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** that employee is scoped to the visit's region

#### Scenario: Proposal respects working hours
- **WHEN** a proposed schedule assigns a service visit to an employee with a proposed planned start and end time
- **THEN** that time window falls entirely within the employee's working hours

#### Scenario: Proposal avoids double-booking
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** the proposed time window does not overlap the time window of any other visit already assigned to that employee, or any other visit proposed to that employee in the same schedule

### Requirement: Proposed schedule keeps each visit's requested date
The system SHALL propose a planned start time for a service visit only on that visit's own requested date; the system SHALL NOT propose moving a visit to a different date.

#### Scenario: Proposed time stays on the visit's requested date
- **WHEN** a proposed schedule assigns a service visit to an employee
- **THEN** the proposed planned start time falls on that visit's requested date

### Requirement: Proposed schedule minimizes travel distance
Among schedules that satisfy the hard constraints, the system SHALL prefer a schedule that reduces the total geographic travel distance between the visits proposed to the same employee on the same day.

#### Scenario: Lower-travel schedule is preferred
- **WHEN** more than one feasible schedule exists for the same set of unassigned visits
- **THEN** the system proposes one with no greater total travel distance, per employee per day, than the alternatives it considered

### Requirement: A schedule run never alters existing assignments
The system SHALL treat every already-assigned service visit as fixed when generating a proposed schedule: its employee and time window SHALL NOT be changed by the run, and it counts toward that employee's existing commitments for the hard constraints.

#### Scenario: Existing assignment is unaffected by generating a proposal
- **WHEN** a proposed schedule is generated while a service visit already has an assignment
- **THEN** that assignment's employee and time window are unchanged, and the proposal does not reassign that visit

### Requirement: Review and apply a proposed schedule
The system SHALL let a user apply a previously generated proposed schedule, creating a real assignment for each visit the proposal scheduled, using the same rules as manually assigning a visit (including rejecting any visit that is no longer unassigned at the time of applying).

#### Scenario: Planner applies a proposed schedule
- **WHEN** a user applies a proposed schedule
- **THEN** the system creates an assignment for each service visit the proposal scheduled, using the proposal's employee and planned start time, and each affected visit's status becomes assigned

#### Scenario: Applying skips a visit assigned since the proposal was generated
- **WHEN** a user applies a proposed schedule and one of its visits is no longer unassigned
- **THEN** the system does not create a second assignment for that visit, applies the rest of the proposal, and reports that visit as skipped
