# driving-times Specification

## Purpose

Persists a region-scoped driving-time matrix sourced from TomTom, so the route optimizer can prefer schedules that are genuinely faster to drive rather than merely closer in a straight line.

## Requirements

### Requirement: Driving-time matrix data model
The system SHALL persist, for a region, a single driving time in minutes for each ordered pair of that region's location endpoints. This is a static, typical driving time — not conditioned on time of day, day of week, or current traffic. Driving time from location A to location B SHALL be stored independently of driving time from location B to location A.

#### Scenario: An entry is persisted with its full key
- **WHEN** a driving-time entry is stored for a region and an ordered pair of locations
- **THEN** the system persists the duration in minutes and it is retrievable by that same region and ordered pair

#### Scenario: Reverse direction is independent
- **WHEN** the driving time from location A to location B is stored
- **THEN** the driving time from location B to location A is a separate entry, not implied or derived from it

### Requirement: A region's driving-time matrix covers its customer locations and scoped employees
The system SHALL treat a region's location endpoints, for driving-time purposes, as the union of: every non-deleted customer location currently assigned to that region, and the home location of every non-deleted employee currently scoped to that region.

#### Scenario: Customer locations in the region are included
- **WHEN** a region's driving-time matrix is computed
- **THEN** every non-deleted customer location currently assigned to that region is a location endpoint

#### Scenario: Employees scoped to the region are included
- **WHEN** a region's driving-time matrix is computed
- **THEN** the home location of every non-deleted employee currently scoped to that region is a location endpoint

#### Scenario: An employee scoped to multiple regions appears in each
- **WHEN** an employee is scoped to more than one region
- **THEN** that employee's home location is a location endpoint in every region's driving-time matrix they are scoped to

### Requirement: Compute a region's driving-time matrix from TomTom on demand
The system SHALL let a user trigger computation of a region's driving-time matrix. Computing SHALL query the TomTom Matrix Routing API v2 — the specific TomTom product this capability depends on, available under a free TomTom Developer account — once for that region's current full set of location endpoints, and SHALL replace any previously stored driving-time entries for that region with the newly computed ones. This action SHALL be manual and on demand — it SHALL NOT run automatically as a result of any other action (customer location sync, region geo-shape edits, employee region changes, or another region's computation).

#### Scenario: The system depends on TomTom's Matrix Routing API v2
- **WHEN** a region's driving-time matrix is computed
- **THEN** the system calls TomTom's Matrix Routing API v2, and no other TomTom product, to obtain the driving times

#### Scenario: Triggering computation for a region
- **WHEN** a user triggers driving-time computation for a region
- **THEN** the system queries TomTom for that region's current location endpoints and persists the resulting durations

#### Scenario: Recomputing replaces previous entries
- **WHEN** a region's driving-time matrix is recomputed after having been computed before
- **THEN** the previous entries for that region are replaced by the newly computed ones, not merged or appended

#### Scenario: Computation does not run automatically
- **WHEN** a region's geo-shape is edited, a customer location's region changes, or an employee's regions change
- **THEN** no driving-time computation is triggered as a result

### Requirement: Computing a region's driving-time matrix tolerates individual routing failures
The system SHALL continue computing the remaining entries of a region's driving-time matrix when TomTom cannot return a route for a specific location pair (for example, an unroutable location or a transient API error), rather than aborting the entire computation. The unresolvable entry SHALL simply not be stored.

#### Scenario: One unroutable pair does not block the rest
- **WHEN** a region's driving-time computation is triggered and TomTom cannot return a route for one location pair
- **THEN** the system still stores the entries it could successfully compute, and does not store an entry for the failed pair

### Requirement: Driving time is looked up by region and ordered location pair
The system SHALL provide the stored driving time in minutes for an ordered pair of locations when an entry exists; it SHALL indicate no entry exists otherwise, rather than returning an estimated or default value.

#### Scenario: A computed entry is retrievable
- **WHEN** a driving-time entry has been computed for an ordered pair of locations
- **THEN** a lookup for that same pair returns the stored duration in minutes

#### Scenario: An uncomputed entry is reported as absent
- **WHEN** a lookup is made for an ordered pair of locations that has no stored entry
- **THEN** the system reports that no driving time is available for that pair, rather than returning a value

### Requirement: TomTom credentials stay server-side
The system SHALL NOT expose TomTom API credentials to the frontend; all communication with TomTom SHALL happen through the backend.

#### Scenario: Frontend never receives TomTom credentials
- **WHEN** the frontend triggers a region's driving-time computation or displays computed driving-time data
- **THEN** no TomTom credential or API key is present in any response the frontend receives
