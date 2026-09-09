## REMOVED Requirements

### Requirement: Proposed schedule minimizes travel distance
**Reason**: Straight-line distance is replaced by driving time sourced from the driving-times capability, which reflects road networks and time-of-day traffic instead of geographic proximity.
**Migration**: See "Proposed schedule minimizes travel time" below.

## ADDED Requirements

### Requirement: Proposed schedule minimizes travel time
Among schedules that satisfy the hard constraints, the system SHALL prefer a schedule that reduces total driving time: between visits proposed to the same employee on the same day, and from that employee's home location to their visits that day. Driving time between two locations SHALL be looked up from that pair's region driving-time matrix. A location pair with no matching driving-time entry — because it has not yet been computed, or because it crosses a region boundary for an employee scoped to multiple regions — SHALL fall back to a distance-based estimate for that pair only, so travel time is never treated as free or omitted for a pair that has no computed entry.

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
