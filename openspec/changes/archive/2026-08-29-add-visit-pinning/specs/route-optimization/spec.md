## ADDED Requirements

### Requirement: Only pinned assignments are fixed during a schedule run
The system SHALL treat only pinned assignments as fixed when generating a proposed schedule: a pinned assignment's employee and time window SHALL NOT be changed, and it counts toward that employee's existing commitments for the hard constraints. Every other visit — unassigned, or assigned but not pinned — SHALL be treated as a candidate the schedule run may assign or reassign.

#### Scenario: Pinned assignment is unaffected by generating a proposal
- **WHEN** a proposed schedule is generated while a service visit has a pinned assignment
- **THEN** that assignment's employee and time window are unchanged, and the proposal does not reassign that visit

#### Scenario: Unpinned assigned visit becomes a candidate for the schedule run
- **WHEN** a proposed schedule is generated while a service visit has an assignment that is not pinned
- **THEN** the proposal may assign that visit to the same or a different employee and/or time than its current assignment, subject to the hard constraints

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

## MODIFIED Requirements

### Requirement: Generate a proposed schedule
The system SHALL let a user request a proposed schedule covering every service visit that does not currently have a pinned assignment — whether it is unassigned or already has an unpinned assignment — computed from the current employees, all service visits, and all pinned assignments, without creating or changing any assignment as a result of generating the proposal.

#### Scenario: Planner requests a proposed schedule
- **WHEN** a user requests a proposed schedule
- **THEN** the system returns a proposal that, for each service visit without a pinned assignment, either names the employee and planned start/end time it proposes for that visit, or leaves it unscheduled if no feasible assignment exists, and no assignment is created or changed as a result

## REMOVED Requirements

### Requirement: A schedule run never alters existing assignments
**Reason**: Superseded by pin-aware scheduling — a schedule run may now alter an existing assignment as long as it isn't pinned.
**Migration**: See "Only pinned assignments are fixed during a schedule run".

### Requirement: Review and apply a proposed schedule
**Reason**: Superseded by a pin-aware version that can update an existing unpinned assignment in place, and that skips a visit based on it having become pinned rather than solely on it being unassigned.
**Migration**: See "Applying a proposed schedule creates or updates assignments".
