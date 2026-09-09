## MODIFIED Requirements

### Requirement: Create, update, and soft-delete a contract line
The system SHALL allow a user to create a contract line under a contract for one of that contract's customer's locations, update its customer location, dates, interval, duration, and required products, and soft-delete it. A soft-deleted contract line SHALL NOT be permanently removed.

#### Scenario: Creating a contract line
- **WHEN** a user creates a contract line under a contract, specifying a customer location, start date, interval, duration, and required products
- **THEN** the system persists a new contract line linked to that contract and customer location, and generates its service visits per the service-visits capability's generation rule

#### Scenario: Updating a contract line
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required products
- **THEN** the system persists the change and regenerates the line's not-yet-started service visits per the service-visits capability's regeneration rule

#### Scenario: Soft-deleting a contract line
- **WHEN** a user soft-deletes a contract line
- **THEN** the system marks it deleted rather than removing it, it no longer appears in the default contract line list, and any service visits generated from it (and any assignment made against one of those visits) are permanently removed
