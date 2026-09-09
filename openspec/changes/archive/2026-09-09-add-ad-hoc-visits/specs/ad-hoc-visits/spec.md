## Purpose

Lets a contract line's next visit be booked directly into a specific open slot, immediately assigned, instead of waiting for the line's regular recurrence to generate it — the foundation for customer self-service slot picking, staff-operated for now.

## ADDED Requirements

### Requirement: Free slots are found for a contract line
The system SHALL, given a contract line, return every candidate free slot over the next 14 days: an employee, a date, and a start/end time such that the employee possesses every skill the contract line requires, is scoped to the contract line's customer location's region, has a resolved working-hours window on that date with the slot's start/end time falling entirely within it, and has no time overlap between the slot and any other visit already assigned to them that date. A contract line with no candidate slots SHALL return an empty result rather than an error.

#### Scenario: Slots are found across qualifying employees and dates
- **WHEN** free slots are requested for a contract line
- **THEN** the system returns every (employee, date, start/end time) combination over the next 14 days satisfying the skill, region, working-hours, and non-overlap conditions

#### Scenario: An employee without a required skill is never offered
- **WHEN** free slots are requested for a contract line requiring a skill an employee does not hold
- **THEN** no slot naming that employee is returned

#### Scenario: An employee outside the contract line's region is never offered
- **WHEN** free slots are requested for a contract line whose customer location is in a region an employee is not scoped to
- **THEN** no slot naming that employee is returned

#### Scenario: A fully booked employee-day yields no slot that day
- **WHEN** an otherwise-qualifying employee's existing assignments leave no gap of at least the contract line's duration within their working hours on a given date
- **THEN** no slot names that employee on that date

#### Scenario: No qualifying employee exists
- **WHEN** free slots are requested for a contract line and no employee satisfies the skill and region conditions
- **THEN** the system returns an empty result rather than an error

### Requirement: Booking a free slot creates an immediately assigned visit
The system SHALL let a user book one of a contract line's returned free slots. Booking SHALL create a new service visit for that contract line at the slot's date, and assign it to the slot's employee at the slot's start/end time in the same action, using the same assignment mechanics as manually assigning any other visit. The resulting visit's status SHALL be assigned; it SHALL NOT pass through an unassigned state.

#### Scenario: Booking creates a visit and its assignment together
- **WHEN** a user books a free slot for a contract line
- **THEN** the system creates a new service visit for that contract line at the slot's date, with an assignment to the slot's employee and time, and the visit's status is assigned

#### Scenario: A booked ad-hoc visit is otherwise an ordinary visit
- **WHEN** an ad-hoc visit has been booked
- **THEN** it is retrievable, displayable, and reassignable through the same APIs and views as any other service visit, with no distinguishing marker required by this capability
