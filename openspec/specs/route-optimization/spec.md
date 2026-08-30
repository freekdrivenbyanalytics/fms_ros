# route-optimization Specification

## Purpose

Proposes an optimized employee/visit schedule for every currently unassigned service visit, respecting each employee's skills, region, working hours, and existing commitments, and minimizing travel between an employee's visits — for a planner to review and apply as real assignments.

## Requirements

### Requirement: Generate a proposed schedule
The system SHALL let a user request a proposed schedule covering every service visit that does not currently have a pinned assignment — whether it is unassigned or already has an unpinned assignment — computed from the current employees, all service visits, and all pinned assignments, without creating or changing any assignment as a result of generating the proposal.

#### Scenario: Planner requests a proposed schedule
- **WHEN** a user requests a proposed schedule
- **THEN** the system returns a proposal that, for each service visit without a pinned assignment, either names the employee and planned start/end time it proposes for that visit, or leaves it unscheduled if no feasible assignment exists, and no assignment is created or changed as a result

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

### Requirement: Proposed schedule keeps each visit's effective schedule date
The system SHALL propose a planned start time for a service visit only on that visit's effective schedule date — its own requested date if that date has not yet passed, or today if it has — and SHALL NOT propose any other date.

#### Scenario: Proposed time stays on the visit's requested date when not yet passed
- **WHEN** a proposed schedule assigns a service visit whose requested date has not passed
- **THEN** the proposed planned start time falls on that visit's requested date

#### Scenario: A visit whose requested date has passed is rescheduled to today
- **WHEN** a proposed schedule assigns a service visit whose requested date has already passed
- **THEN** the proposed planned start time falls on today's date rather than the original requested date

### Requirement: Proposed schedule minimizes travel distance
Among schedules that satisfy the hard constraints, the system SHALL prefer a schedule that reduces the total geographic travel distance between the visits proposed to the same employee on the same day.

#### Scenario: Lower-travel schedule is preferred
- **WHEN** more than one feasible schedule exists for the same set of unassigned visits
- **THEN** the system proposes one with no greater total travel distance, per employee per day, than the alternatives it considered

### Requirement: Only pinned assignments are fixed during a schedule run
The system SHALL treat only pinned assignments as fixed when generating a proposed schedule: a pinned assignment's employee and time window SHALL NOT be changed, and it counts toward that employee's existing commitments for the hard constraints. Every other visit — unassigned, or assigned but not pinned — SHALL be treated as a candidate the schedule run may assign or reassign.

#### Scenario: Pinned assignment is unaffected by generating a proposal
- **WHEN** a proposed schedule is generated while a service visit has a pinned assignment
- **THEN** that assignment's employee and time window are unchanged, and the proposal does not reassign that visit

#### Scenario: Unpinned assigned visit becomes a candidate for the schedule run
- **WHEN** a proposed schedule is generated while a service visit has an assignment that is not pinned
- **THEN** the proposal may assign that visit to the same or a different employee and/or time than its current assignment, subject to the hard constraints

#### Scenario: An already-started assignment is fixed even without manual pinning
- **WHEN** a proposed schedule is generated while a service visit has an assignment whose planned start time has already passed
- **THEN** that assignment is treated as fixed exactly like a manually pinned one, and the proposal does not reassign that visit

### Requirement: Applying a proposed schedule creates or updates assignments
The system SHALL let a user apply a previously generated proposed schedule: for each visit the proposal scheduled, the system creates a new assignment if the visit is currently unassigned, or updates its existing assignment's employee and planned start/end time in place if the visit is currently assigned and unpinned, using the same rules as manually assigning a visit. The system SHALL reject applying a visit that has become pinned since the proposal was generated, reporting it as skipped rather than overwriting its now-protected assignment.

#### Scenario: Planner applies a proposed schedule for a previously unassigned visit
- **WHEN** a user applies a proposed schedule and one of its visits was unassigned at the time of applying
- **THEN** the system creates an assignment for that visit using the proposal's employee and planned start time, and the visit's status becomes assigned

#### Scenario: Planner applies a proposed schedule that moves an existing unpinned assignment
- **WHEN** a user applies a proposed schedule and one of its visits already has an unpinned assignment at the time of applying
- **THEN** the system updates that assignment's employee and planned start/end time to match the proposal, rather than creating a second assignment

#### Scenario: Applying skips a visit pinned since the proposal was generated
- **WHEN** a user applies a proposed schedule and one of its visits has become pinned since the proposal was generated
- **THEN** the system does not change that visit's assignment, applies the rest of the proposal, and reports that visit as skipped
