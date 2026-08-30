## ADDED Requirements

### Requirement: Proposed schedule excludes visits without geocoded coordinates
The system SHALL NOT propose scheduling a service visit whose customer location has no resolved geographic coordinates, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit at an ungeocoded location is never scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's customer location has no resolved latitude/longitude
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required skills, region, and availability exists

### Requirement: Proposed schedule excludes visits without an assigned region
The system SHALL NOT propose scheduling a service visit whose customer location has no assigned region, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit at a regionless location is never scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's customer location has no assigned region
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required skills, coordinates, and availability exists
