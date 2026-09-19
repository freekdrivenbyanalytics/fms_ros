# Spec Delta

## ADDED Requirements

### Requirement: A proposed schedule run's start-from time is configurable for today
The system SHALL let a user requesting a proposed schedule specify a time of day, defaulting to 08:00, before which no visit is proposed to start *today*. For today's date only, an employee's working-hours start used by the run SHALL be the later of their normal resolved working-hours start and this time; for every other date in the run's scheduling window, the employee's normal resolved working-hours start SHALL be used unchanged.

#### Scenario: Default start-from time
- **WHEN** a user requests a proposed schedule without specifying a start-from time
- **THEN** the run does not propose any visit today starting before 08:00, and every other day in the window uses each employee's normal working-hours start unchanged

#### Scenario: A later start-from time excludes earlier slots today
- **WHEN** a user requests a proposed schedule with a start-from time later than an employee's normal working-hours start today
- **THEN** the run does not propose that employee any visit today starting before the specified time

#### Scenario: An earlier start-from time never moves an employee's start earlier
- **WHEN** a user requests a proposed schedule with a start-from time earlier than an employee's normal working-hours start today
- **THEN** the run still does not propose that employee any visit today before their normal working-hours start

#### Scenario: Start-from time does not affect later days
- **WHEN** a user requests a proposed schedule spanning more than one day with a start-from time
- **THEN** every day after today in the run uses each employee's normal working-hours start, unaffected by the start-from time
