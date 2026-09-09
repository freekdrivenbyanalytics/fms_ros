## MODIFIED Requirements

### Requirement: Generate a proposed schedule
The system SHALL let a user request a proposed schedule covering every service visit whose effective schedule date is today or tomorrow and that does not currently have a pinned assignment — whether it is unassigned or already has an unpinned assignment — computed from the current employees, those service visits, and all pinned assignments, without creating or changing any assignment as a result of generating the proposal.

#### Scenario: Planner requests a proposed schedule
- **WHEN** a user requests a proposed schedule
- **THEN** the system returns a proposal that, for each service visit whose effective schedule date is today or tomorrow and that has no pinned assignment, either names the employee and planned start/end time it proposes for that visit, or leaves it unscheduled if no feasible assignment exists, and no assignment is created or changed as a result

## ADDED Requirements

### Requirement: Proposed schedule excludes visits outside the scheduling window
The system SHALL NOT propose scheduling a service visit whose effective schedule date is not today or tomorrow, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit requested further in the future is not scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's effective schedule date is neither today nor tomorrow
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required skills, region, and availability exists

#### Scenario: A visit rolls into the window as time passes
- **WHEN** a service visit's effective schedule date, previously beyond tomorrow, becomes today or tomorrow
- **THEN** a subsequently generated proposed schedule considers that visit like any other candidate
