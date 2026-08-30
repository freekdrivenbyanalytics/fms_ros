## ADDED Requirements

### Requirement: Proposed schedule keeps each visit's effective schedule date
The system SHALL propose a planned start time for a service visit only on that visit's effective schedule date — its own requested date if that date has not yet passed, or today if it has — and SHALL NOT propose any other date.

#### Scenario: Proposed time stays on the visit's requested date when not yet passed
- **WHEN** a proposed schedule assigns a service visit whose requested date has not passed
- **THEN** the proposed planned start time falls on that visit's requested date

#### Scenario: A visit whose requested date has passed is rescheduled to today
- **WHEN** a proposed schedule assigns a service visit whose requested date has already passed
- **THEN** the proposed planned start time falls on today's date rather than the original requested date

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Proposed schedule keeps each visit's requested date
**Reason**: Superseded — a visit whose requested date has already passed may now be rescheduled to today rather than being stuck on a date that's already gone.
**Migration**: See "Proposed schedule keeps each visit's effective schedule date".
