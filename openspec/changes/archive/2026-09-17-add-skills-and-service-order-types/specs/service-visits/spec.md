## MODIFIED Requirements

### Requirement: Service visit data model
The system SHALL persist each service visit with a unique identifier, the contract line it was generated from, requested date, and a status; duration, product requirements, required skills, and priority are read through the contract line.

#### Scenario: Service visit is persisted with required fields
- **WHEN** a service visit is created with id, contract_line_id, and requested_date
- **THEN** the system persists the service visit and all fields are retrievable unchanged, with customer name, address, region, duration, required products, required skills, and priority available through the contract line

### Requirement: List service visits by assignment status
The system SHALL provide an API to retrieve service visits with their status, their contract line's customer location (customer name, address, region), duration, required products, and required skills (the union of the skills required by those products), so unassigned visits and assigned visits can be distinguished, located, and matched to a qualified employee. The API SHALL accept optional start-date and end-date filters that restrict the returned visits to those whose requested_date falls within the given range (inclusive); omitting either bound leaves that side of the range open.

#### Scenario: Retrieve visits with status
- **WHEN** a client requests the list of service visits
- **THEN** the system returns every visit together with its status of either `unassigned` or `assigned`, and the customer name, address, region, duration, required products, and required skills of the contract line it was generated from

#### Scenario: Retrieve visits within a date range
- **WHEN** a client requests the list of service visits with a start-date and/or end-date filter
- **THEN** the system returns only visits whose requested_date falls within the given range, applying only the bounds that were provided

#### Scenario: No date filter returns every visit
- **WHEN** a client requests the list of service visits with no start-date or end-date filter
- **THEN** the system returns every visit regardless of requested_date, unchanged from today's behavior
