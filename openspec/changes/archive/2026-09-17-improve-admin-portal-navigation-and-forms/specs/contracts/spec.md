## MODIFIED Requirements

### Requirement: Contract Line data model
The system SHALL persist each contract line with a unique identifier, the contract it belongs to, the customer location it applies to, a start date, an optional end date, a recurrence interval expressed as an interval unit (`week`, `month`, or `quarter`) and an interval count, a visit duration in minutes, the products it requires, a priority (1 = high, 2 = medium, 3 = low, defaulting to 2), and a soft-delete flag.

#### Scenario: Contract line is persisted with required fields
- **WHEN** a contract line is created with id, contract_id, customer_location_id, start_date, interval_unit, interval_count, duration_minutes, and one or more required products
- **THEN** the system persists the contract line and all fields are retrievable unchanged, with no end date unless one was given and a priority of 2 unless one was given

### Requirement: Create, update, and soft-delete a contract line
The system SHALL allow a user to create a contract line under a contract for one of that contract's customer's locations, update its customer location, dates, interval unit and count, duration, priority, and required products, and soft-delete it. A soft-deleted contract line SHALL NOT be permanently removed.

#### Scenario: Creating a contract line
- **WHEN** a user creates a contract line under a contract, specifying a customer location, start date, interval unit and count, duration, and required products
- **THEN** the system persists a new contract line linked to that contract and customer location, with a priority of 2 unless one was specified, and generates its service visits per the service-visits capability's generation rule

#### Scenario: Creating a contract line with an explicit priority
- **WHEN** a user creates a contract line specifying a priority of 1 or 3
- **THEN** the system persists that priority instead of the default

#### Scenario: Updating a contract line
- **WHEN** a user updates a contract line's customer location, dates, interval unit or count, duration, priority, or required products
- **THEN** the system persists the change and regenerates the line's not-yet-started service visits per the service-visits capability's regeneration rule

#### Scenario: Soft-deleting a contract line
- **WHEN** a user soft-deletes a contract line
- **THEN** the system marks it deleted rather than removing it, it no longer appears in the default contract line list, and any service visits generated from it (and any assignment made against one of those visits) are permanently removed

## ADDED Requirements

### Requirement: A contract line's recurrence interval is limited to a fixed set of combinations
The system SHALL only accept an interval unit and count combination from a fixed set: `week` with a count of 1, 2, 3, or 4; `month` with a count of 1, 2, or 3; or `quarter` with a count of 1. The system SHALL reject any other combination.

#### Scenario: A supported combination is accepted
- **WHEN** a user creates or updates a contract line with an interval unit and count from the supported set
- **THEN** the system persists the contract line

#### Scenario: An unsupported combination is rejected
- **WHEN** a user creates or updates a contract line with an interval unit and count outside the supported set (for example, 5 weeks, or a count of 2 for quarter)
- **THEN** the system rejects the request and does not persist the change
