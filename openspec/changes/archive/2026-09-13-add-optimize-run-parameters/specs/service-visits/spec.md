## MODIFIED Requirements

### Requirement: Service visit data model
The system SHALL persist each service visit with a unique identifier, the contract line it was generated from, requested date, and a status; duration, product requirements, and priority are read through the contract line.

#### Scenario: Service visit is persisted with required fields
- **WHEN** a service visit is created with id, contract_line_id, and requested_date
- **THEN** the system persists the service visit and all fields are retrievable unchanged, with customer name, address, region, duration, required products, and priority available through the contract line
