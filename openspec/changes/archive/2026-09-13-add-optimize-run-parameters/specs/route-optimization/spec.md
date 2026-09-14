## MODIFIED Requirements

### Requirement: Generate a proposed schedule
The system SHALL let a user request a proposed schedule covering every service visit whose effective schedule date falls within the run's scheduling window and that does not currently have a pinned assignment — whether it is unassigned or already has an unpinned assignment — computed from the current employees, those service visits, and all pinned assignments, without creating or changing any assignment as a result of generating the proposal.

#### Scenario: Planner requests a proposed schedule
- **WHEN** a user requests a proposed schedule
- **THEN** the system returns a proposal that, for each service visit whose effective schedule date falls within the run's scheduling window and that has no pinned assignment, either names the employee and planned start/end time it proposes for that visit, or leaves it unscheduled if no feasible assignment exists, and no assignment is created or changed as a result

### Requirement: Proposed schedule excludes visits outside the scheduling window
The system SHALL NOT propose scheduling a service visit whose effective schedule date falls outside the run's scheduling window, regardless of whether an otherwise-feasible assignment exists for it.

#### Scenario: A visit requested further in the future is not scheduled
- **WHEN** a proposed schedule is generated and a candidate service visit's effective schedule date falls outside the run's scheduling window
- **THEN** the proposal does not assign that visit to any employee, and it is reported as unscheduled even if an employee with the required products, region, and availability exists

#### Scenario: A visit rolls into the window as time passes
- **WHEN** a service visit's effective schedule date, previously outside the run's scheduling window, becomes within it
- **THEN** a subsequently generated proposed schedule considers that visit like any other candidate

## ADDED Requirements

### Requirement: A proposed schedule run's scheduling window is configurable
The system SHALL let a user requesting a proposed schedule specify how many days ahead of today the run's scheduling window extends, defaulting to 2 (today and tomorrow, matching prior behavior) and capped at 14. The run's scheduling window SHALL be today through today plus that number of days minus one.

#### Scenario: Default window matches prior behavior
- **WHEN** a user requests a proposed schedule without specifying a days-ahead value
- **THEN** the run's scheduling window is today and tomorrow

#### Scenario: A larger window includes visits further out
- **WHEN** a user requests a proposed schedule with a days-ahead value of 5
- **THEN** the run's scheduling window is today through four days from today, and service visits whose effective schedule date falls in that range are candidates

#### Scenario: An excessive days-ahead value is capped
- **WHEN** a user requests a proposed schedule with a days-ahead value greater than 14
- **THEN** the system uses a scheduling window of 14 days instead of the requested value

### Requirement: A proposed schedule run's solver time budget is configurable
The system SHALL let a user requesting a proposed schedule specify how many seconds the solver may spend on that run, defaulting to the system's prior fixed time budget when not specified.

#### Scenario: Default time budget matches prior behavior
- **WHEN** a user requests a proposed schedule without specifying a time budget
- **THEN** the solver runs for the same fixed time budget it used before this parameter existed

#### Scenario: A custom time budget is honored
- **WHEN** a user requests a proposed schedule with an explicit time budget
- **THEN** the solver's run is bounded by that time budget instead of the default

### Requirement: Proposed schedule prioritizes higher-priority and more urgent visits when not everything can be scheduled
Among schedules that satisfy the hard constraints, the system SHALL prefer a schedule that leaves fewer visits unscheduled, as before. When a schedule cannot avoid leaving some visits unscheduled, the system SHALL prefer leaving out lower-priority visits over higher-priority ones — a single higher-priority (numerically lower) visit left unscheduled SHALL always be considered worse than any number of lower-priority visits left unscheduled — and, among unscheduled visits of the same priority, SHALL prefer leaving out ones with a later effective schedule date over ones due sooner.

#### Scenario: A higher-priority visit is scheduled ahead of lower-priority ones when capacity is tight
- **WHEN** not every candidate visit can be scheduled within the hard constraints, and a higher-priority visit competes with one or more lower-priority visits for the same capacity
- **THEN** the proposal schedules the higher-priority visit, even if that means leaving more lower-priority visits unscheduled than would otherwise be necessary

#### Scenario: A more urgent visit is scheduled ahead of a less urgent one of the same priority
- **WHEN** not every candidate visit can be scheduled within the hard constraints, and two visits of the same priority but different effective schedule dates compete for the same capacity
- **THEN** the proposal schedules the one with the sooner effective schedule date
