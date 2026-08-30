## MODIFIED Requirements

### Requirement: Service visit data model
The system SHALL persist each service visit with a unique identifier, the contract line it was generated from, requested date, and a status; duration and skill requirements are read through the contract line.

#### Scenario: Service visit is persisted with required fields
- **WHEN** a service visit is created with id, contract_line_id, and requested_date
- **THEN** the system persists the service visit and all fields are retrievable unchanged, with customer name, address, region, duration, and required skills available through the contract line

### Requirement: List service visits by assignment status
The system SHALL provide an API to retrieve service visits with their status, their contract line's customer location (customer name, address, region), duration, and required skills, so unassigned visits and assigned visits can be distinguished, located, and matched to a qualified employee.

#### Scenario: Retrieve visits with status
- **WHEN** a client requests the list of service visits
- **THEN** the system returns every visit together with its status of either `unassigned` or `assigned`, and the customer name, address, region, duration, and required skills of the contract line it was generated from
