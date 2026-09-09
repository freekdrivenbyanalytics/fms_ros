## MODIFIED Requirements

### Requirement: Free slots are found for a contract line
The system SHALL, given a contract line, return every candidate free slot over the next 14 days: an employee, a date, and a start/end time such that the employee possesses every product the contract line requires, is scoped to the contract line's customer location's region, has a resolved working-hours window on that date with the slot's start/end time falling entirely within it, and has no time overlap between the slot and any other visit already assigned to them that date. A contract line with no candidate slots SHALL return an empty result rather than an error.

#### Scenario: Slots are found across qualifying employees and dates
- **WHEN** free slots are requested for a contract line
- **THEN** the system returns every (employee, date, start/end time) combination over the next 14 days satisfying the product, region, working-hours, and non-overlap conditions

#### Scenario: An employee without a required skill is never offered
- **WHEN** free slots are requested for a contract line requiring a product an employee does not hold
- **THEN** no slot naming that employee is returned

#### Scenario: An employee outside the contract line's region is never offered
- **WHEN** free slots are requested for a contract line whose customer location is in a region an employee is not scoped to
- **THEN** no slot naming that employee is returned

#### Scenario: A fully booked employee-day yields no slot that day
- **WHEN** an otherwise-qualifying employee's existing assignments leave no gap of at least the contract line's duration within their working hours on a given date
- **THEN** no slot names that employee on that day

#### Scenario: No qualifying employee exists
- **WHEN** free slots are requested for a contract line and no employee satisfies the product and region conditions
- **THEN** the system returns an empty result rather than an error
