## ADDED Requirements

### Requirement: A proposed schedule run's execution mode is configurable
The system SHALL let a user requesting a proposed schedule choose an execution mode: `single` (the default, matching all prior behavior — the entire run solved as one problem) or `parallel`. In `parallel` mode, the system SHALL partition the run's regions into groups such that two regions are in the same group whenever any employee is scoped to both (directly or transitively through a chain of shared employees), and SHALL solve each group's visits and employees as an independent problem, concurrently with every other group, before merging every group's results into one proposal in the same shape `single` mode returns. The system SHALL NOT let two concurrently solved groups consider the same employee, so no employee can be double-booked as a result of parallel solving.

#### Scenario: Default mode matches prior behavior
- **WHEN** a user requests a proposed schedule without specifying an execution mode
- **THEN** the run solves as a single problem, exactly as before this parameter existed

#### Scenario: Parallel mode partitions independent regions
- **WHEN** a user requests a proposed schedule with `parallel` mode and the run's regions split into two or more groups sharing no employee between groups
- **THEN** the system solves each group concurrently and returns one merged proposal covering every group's visits

#### Scenario: An employee scoped to two regions keeps those regions together
- **WHEN** a user requests a proposed schedule with `parallel` mode and an employee is scoped to two regions that would otherwise be separate groups
- **THEN** the system solves those two regions together as a single group, never splitting them across concurrent solves

#### Scenario: Fully connected regions fall back to a single solve
- **WHEN** a user requests a proposed schedule with `parallel` mode and every region in scope for the run is connected to every other, directly or transitively, through shared employees
- **THEN** the system solves the run as a single problem, identical to `single` mode, rather than erroring or solving nothing

#### Scenario: Parallel mode never double-books an employee across groups
- **WHEN** a proposed schedule is generated in `parallel` mode
- **THEN** no employee appears in more than one concurrently solved group, so no employee can receive conflicting proposed assignments from two different groups
