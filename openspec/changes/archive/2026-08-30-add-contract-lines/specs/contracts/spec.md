## ADDED Requirements

### Requirement: Contract Line data model
The system SHALL persist each contract line with a unique identifier, the contract it belongs to, the customer location it applies to, a start date, an optional end date, an interval in days, a visit duration in minutes, the skills it requires, and a soft-delete flag.

#### Scenario: Contract line is persisted with required fields
- **WHEN** a contract line is created with id, contract_id, customer_location_id, start_date, interval_days, duration_minutes, and one or more required skills
- **THEN** the system persists the contract line and all fields are retrievable unchanged, with no end date unless one was given

### Requirement: A contract can have multiple lines
The system SHALL allow a contract to have one or more contract lines.

#### Scenario: Contract with multiple lines
- **WHEN** a contract has two or more contract lines persisted with its contract_id
- **THEN** each line is retrievable and associated with that contract

### Requirement: A contract line can require multiple skills
The system SHALL allow a contract line to require more than one skill.

#### Scenario: Contract line with multiple required skills
- **WHEN** a contract line is associated with two or more skills
- **THEN** each association is retrievable and the contract line's required skills include all of them

### Requirement: Create, update, and soft-delete a contract
The system SHALL allow a user to create a contract for a customer, update which customer it belongs to, and soft-delete it. A soft-deleted contract SHALL NOT be permanently removed.

#### Scenario: Creating a contract
- **WHEN** a user creates a contract for a customer
- **THEN** the system persists a new contract linked to that customer, with no contract lines yet

#### Scenario: Updating a contract
- **WHEN** a user updates a contract's customer
- **THEN** the system persists the change and the contract is now linked to the new customer

#### Scenario: Soft-deleting a contract
- **WHEN** a user soft-deletes a contract
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default contract list

### Requirement: Create, update, and soft-delete a contract line
The system SHALL allow a user to create a contract line under a contract for one of that contract's customer's locations, update its customer location, dates, interval, duration, and required skills, and soft-delete it. A soft-deleted contract line SHALL NOT be permanently removed.

#### Scenario: Creating a contract line
- **WHEN** a user creates a contract line under a contract, specifying a customer location, start date, interval, duration, and required skills
- **THEN** the system persists a new contract line linked to that contract and customer location, with no service visits generated as a result

#### Scenario: Updating a contract line
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required skills
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract line
- **WHEN** a user soft-deletes a contract line
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default contract line list, while any service visits already generated from it remain unaffected

### Requirement: Soft-deleting a contract cascades to its lines
The system SHALL soft-delete every contract line belonging to a contract when that contract is soft-deleted.

#### Scenario: Deleting a contract deletes its lines
- **WHEN** a user soft-deletes a contract that has one or more contract lines
- **THEN** the system also marks each of those contract lines deleted

### Requirement: Deleted contracts and contract lines are hidden by default
The system SHALL exclude soft-deleted contracts from the contract list, and soft-deleted contract lines from a contract's list of lines, returned to callers by default.

#### Scenario: Deleted contract is excluded from the list
- **WHEN** a caller requests the list of contracts
- **THEN** contracts marked deleted are not included in the result

#### Scenario: Deleted contract line is excluded from its contract's lines
- **WHEN** a caller requests a contract's lines
- **THEN** contract lines marked deleted are not included in the result

## MODIFIED Requirements

### Requirement: Contract data model
The system SHALL persist each contract with a unique identifier, the customer it belongs to, and a soft-delete flag.

#### Scenario: Contract is persisted with required fields
- **WHEN** a contract is created with id and customer_id
- **THEN** the system persists the contract and both fields are retrievable unchanged

## REMOVED Requirements

### Requirement: A contract can require multiple skills
**Reason**: Required skills now belong to a contract line, not a contract directly, since a contract can span multiple locations each needing different skills.
**Migration**: See "A contract line can require multiple skills".
