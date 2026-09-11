## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Proposed schedule leaves enough driving time before an employee's first visit
The system SHALL only propose an employee's first visit of a day starting at or after their working-hours start plus the driving time from their home location to that visit's location, looked up from the region driving-time matrix or, when no matching entry exists, a distance-based estimate.

#### Scenario: First visit of the day accounts for the home-to-visit drive
- **WHEN** a proposed schedule assigns an employee's first visit of a day
- **THEN** that visit's proposed start time is no earlier than the employee's working-hours start time plus the driving time from the employee's home location to the visit's location

#### Scenario: A visit that would require leaving before the drive completes is not proposed
- **WHEN** a candidate placement would start an employee's first visit of the day before their home-to-visit drive could complete from their working-hours start
- **THEN** the system does not propose that placement
