## MODIFIED Requirements

### Requirement: Create, update, and soft-delete a contract line
The system SHALL allow a user to create a contract line under a contract for one of that contract's customer's locations, update its customer location, dates, interval, duration, and required skills, and soft-delete it. A soft-deleted contract line SHALL NOT be permanently removed.

#### Scenario: Creating a contract line
- **WHEN** a user creates a contract line under a contract, specifying a customer location, start date, interval, duration, and required skills
- **THEN** the system persists a new contract line linked to that contract and customer location, and generates its service visits per the service-visits capability's generation rule

#### Scenario: Updating a contract line
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required skills
- **THEN** the system persists the change and does not create, modify, or delete any service visits as a result

#### Scenario: Soft-deleting a contract line
- **WHEN** a user soft-deletes a contract line
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default contract line list, while any service visits already generated from it remain unaffected
