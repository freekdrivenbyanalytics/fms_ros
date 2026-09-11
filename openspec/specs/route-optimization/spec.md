# route-optimization Specification

## Purpose

Proposes an optimized employee/visit schedule for every currently unassigned service visit, respecting each employee's products, region, working hours, and existing commitments, and minimizing travel between an employee's visits — for a planner to review and apply as real assignments.

## Requirements

### Requirement: Generate a proposed schedule
The system SHALL let a user request a proposed schedule covering every service visit whose effective schedule date is today or tomorrow and that does not currently have a pinned assignment — whether it is unassigned or already has an unpinned assignment — computed from the current employees, those service visits, and all pinned assignments, without creating or changing any assignment as a result of generating the proposal.

#### Scenario: Planner requests a proposed schedule
- **WHEN** a user requests a proposed schedule
- **THEN** the system returns a proposal that, for each service visit whose effective schedule date is today or tomorrow and that has no pinned assignment, either names the employee and planned start/end time it proposes for that visit, or leaves it unscheduled if no feasible assignment exists, and no assignment is created or changed as a result

### Requirement: Proposed schedule respects hard constraints
The system SHALL only propose scheduling a service visit to an employee when the employee possesses every product the visit's contract requires, the employee is scoped to the visit's region, the employee has a resolved working-hours window for the visit's proposed date and the visit's proposed time window falls entirely within it, the employee has no time overlap between that proposed visit and any other visit already assigned to them or proposed to them in the same schedule, and the gap between that visit's end (or start) and every other same-day visit of that employee's (proposed or existing) is at least the driving time between their two locations, looked up from the region driving-time matrix or, when no matching entry exists, a distance-based estimate for that pair.

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

#### Scenario: Proposal leaves enough time to drive between two same-day visits
- **WHEN** a proposed schedule assigns two same-day visits to the same employee, one ending before the other starts
- **THEN** the gap between the earlier visit's end time and the later visit's start time is at least the driving time between their two locations

#### Scenario: Proposal rejects a back-to-back placement that leaves no driving time
- **WHEN** a candidate placement would start a visit before the employee could have driven there from the location of their immediately preceding same-day visit
- **THEN** the system does not propose that placement

### Requirement: Proposed schedule keeps each visit's effective schedule date
The system SHALL propose a planned start time for a service visit only on that visit's effective schedule date — its own requested date if that date has not yet passed, or today if it has — and SHALL NOT propose any other date.

#### Scenario: Proposed time stays on the visit's requested date when not yet passed
- **WHEN** a proposed schedule assigns a service visit whose requested date has not passed
- **THEN** the proposed planned start time falls on that visit's requested date

#### Scenario: A visit whose requested date has passed is rescheduled to today
- **WHEN** a proposed schedule assigns a service visit whose requested date has already passed
- **THEN** the proposed planned start time falls on today's date rather than the original requested date

### Requirement: Proposed schedule minimizes travel time
Among schedules that satisfy the hard constraints, the system SHALL prefer a schedule that reduces total driving time: between visits proposed to the same employee on the same day, and from that employee's home location to their visits that day. Driving time between two locations SHALL be looked up from that pair's region driving-time matrix. A location pair with no matching driving-time entry — because it has not yet been computed, or because it crosses a region boundary for an employee scoped to multiple regions — SHALL fall back to a distance-based estimate for that pair only, so travel time is never treated as free or omitted for a pair that has no computed entry. This preference applies on top of the hard driving-time-gap constraint: it minimizes total travel time among schedules that already leave enough of a gap to drive between every pair of same-day visits.

#### Scenario: Lower-travel-time schedule is preferred
- **WHEN** more than one feasible schedule exists for the same set of unassigned visits
- **THEN** the system proposes one with no greater total driving time, per employee per day, than the alternatives it considered

#### Scenario: Travel time between visits uses the driving-time matrix
- **WHEN** a proposed schedule assigns two visits in the same region to the same employee on the same day
- **THEN** the system scores the leg between them using the driving-time entry for that ordered pair

#### Scenario: Employee home-to-visit travel is included
- **WHEN** a proposed schedule assigns one or more visits to an employee on a given day
- **THEN** the system also scores the driving time from that employee's home location to their earliest proposed visit that day, using the driving-time matrix

#### Scenario: Missing driving-time data falls back to a distance-based estimate
- **WHEN** a proposed schedule scores a leg between two locations for which no driving-time entry exists
- **THEN** the system uses a distance-based estimate for that leg instead, rather than treating it as zero cost or excluding it from the score

#### Scenario: A cross-region leg for a multi-region employee falls back to a distance-based estimate
- **WHEN** a proposed schedule assigns an employee scoped to more than one region a pair of same-day visits in two different regions
- **THEN** the system uses a distance-based estimate for the leg between them, since a region's driving-time matrix only covers pairs within that region

### Requirement: Proposed schedule leaves enough driving time before an employee's first visit
The system SHALL only propose an employee's first visit of a day starting at or after their working-hours start plus the driving time from their home location to that visit's location, looked up from the region driving-time matrix or, when no matching entry exists, a distance-based estimate.

#### Scenario: First visit of the day accounts for the home-to-visit drive
- **WHEN** a proposed schedule assigns an employee's first visit of a day
- **THEN** that visit's proposed start time is no earlier than the employee's working-hours start time plus the driving time from the employee's home location to the visit's location

#### Scenario: A visit that would require leaving before the drive completes is not proposed
- **WHEN** a candidate placement would start an employee's first visit of the day before their home-to-visit drive could complete from their working-hours start
- **THEN** the system does not propose that placement

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
