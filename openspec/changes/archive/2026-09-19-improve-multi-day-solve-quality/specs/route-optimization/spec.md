# Spec Delta

## MODIFIED Requirements

### Requirement: A proposed schedule run's execution mode is configurable
The system SHALL let a user requesting a proposed schedule choose an execution mode: `single` (the default) or `parallel`. In `parallel` mode, or in `single` mode when the run's problem size exceeds a configured threshold, the system SHALL partition the run's regions into groups such that two regions are in the same group whenever any employee is scoped to both (directly or transitively through a chain of shared employees), and SHALL solve each group's visits and employees as an independent problem, concurrently with every other group, before merging every group's results into one proposal in the same shape an unsplit solve returns. Below that threshold, `single` mode SHALL solve the entire run as one problem, matching its prior behavior. The system SHALL NOT let two concurrently solved groups consider the same employee, so no employee can be double-booked as a result of splitting, whether triggered by `parallel` mode or by the threshold.

#### Scenario: Default mode matches prior behavior
- **WHEN** a user requests a proposed schedule without specifying an execution mode, and the run's problem size is at or below the threshold
- **THEN** the run solves as a single problem, exactly as before this parameter existed

#### Scenario: A large single-mode run is split automatically
- **WHEN** a user requests a proposed schedule without specifying `parallel` mode, and the run's problem size exceeds the threshold, and the run's regions split into two or more groups sharing no employee between groups
- **THEN** the system solves each group concurrently and returns one merged proposal covering every group's visits, the same way `parallel` mode would

#### Scenario: Parallel mode partitions independent regions
- **WHEN** a user requests a proposed schedule with `parallel` mode and the run's regions split into two or more groups sharing no employee between groups
- **THEN** the system solves each group concurrently and returns one merged proposal covering every group's visits

#### Scenario: An employee scoped to two regions keeps those regions together
- **WHEN** a proposed schedule splits into groups (whether requested as `parallel` or triggered by the threshold) and an employee is scoped to two regions that would otherwise be separate groups
- **THEN** the system solves those two regions together as a single group, never splitting them across concurrent solves

#### Scenario: Fully connected regions fall back to a single solve
- **WHEN** a proposed schedule would otherwise split into groups and every region in scope for the run is connected to every other, directly or transitively, through shared employees
- **THEN** the system solves the run as a single problem, identical to unsplit `single` mode, rather than erroring or solving nothing

#### Scenario: Parallel mode never double-books an employee across groups
- **WHEN** a proposed schedule is generated with its regions split into groups, whether requested as `parallel` or triggered by the threshold
- **THEN** no employee appears in more than one concurrently solved group, so no employee can receive conflicting proposed assignments from two different groups

#### Scenario: A small single-region run below the threshold is never split
- **WHEN** a user requests a proposed schedule without specifying `parallel` mode, the run's problem size is at or below the threshold, and the run's regions would split into two or more groups if `parallel` mode were requested
- **THEN** the system still solves the run as a single problem, since the threshold - not merely a possible split - is what triggers automatic splitting
