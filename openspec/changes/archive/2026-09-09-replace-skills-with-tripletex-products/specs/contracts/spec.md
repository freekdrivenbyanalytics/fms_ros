## MODIFIED Requirements

### Requirement: Contract Line data model
The system SHALL persist each contract line with a unique identifier, the contract it belongs to, the customer location it applies to, a start date, an optional end date, an interval in days, a visit duration in minutes, the products it requires, and a soft-delete flag.

#### Scenario: Contract line is persisted with required fields
- **WHEN** a contract line is created with id, contract_id, customer_location_id, start_date, interval_days, duration_minutes, and one or more required products
- **THEN** the system persists the contract line and all fields are retrievable unchanged, with no end date unless one was given

### Requirement: Create, update, and soft-delete a contract line
The system SHALL allow a user to create a contract line under a contract for one of that contract's customer's locations, update its customer location, dates, interval, duration, and required products, and soft-delete it. A soft-deleted contract line SHALL NOT be permanently removed.

#### Scenario: Creating a contract line
- **WHEN** a user creates a contract line under a contract, specifying a customer location, start date, interval, duration, and required products
- **THEN** the system persists a new contract line linked to that contract and customer location, and generates its service visits per the service-visits capability's generation rule

#### Scenario: Updating a contract line
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required products
- **THEN** the system persists the change and does not create, modify, or delete any service visits as a result

#### Scenario: Soft-deleting a contract line
- **WHEN** a user soft-deletes a contract line
- **THEN** the system marks it deleted rather than removing it, it no longer appears in the default contract line list, and any service visits generated from it (and any assignment made against one of those visits) are permanently removed

## REMOVED Requirements

### Requirement: A contract line can require multiple skills
**Reason**: Skills are replaced by Tripletex-sourced products; see "A contract line can require multiple products" below.
**Migration**: None needed — the same multi-association shape carries over to products.

## ADDED Requirements

### Requirement: A contract line can require multiple products
The system SHALL allow a contract line to require more than one product.

#### Scenario: Contract line with multiple required products
- **WHEN** a contract line is associated with two or more products
- **THEN** each association is retrievable and the contract line's required products include all of them
