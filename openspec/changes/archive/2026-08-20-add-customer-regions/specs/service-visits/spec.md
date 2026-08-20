## MODIFIED Requirements

### Requirement: Service visit data model
The system SHALL persist each service visit with a unique identifier, the customer location it was generated from, duration in minutes, requested date, and a status.

#### Scenario: Service visit is persisted with required fields
- **WHEN** a service visit is created with id, customer_location_id, duration_minutes, and requested_date
- **THEN** the system persists the service visit and all fields are retrievable unchanged, with customer name, address, and region available through the customer location

### Requirement: List service visits by assignment status
The system SHALL provide an API to retrieve service visits with their status and their customer location's customer name, address, and region, so unassigned visits and assigned visits can be distinguished and located.

#### Scenario: Retrieve visits with status
- **WHEN** a client requests the list of service visits
- **THEN** the system returns every visit together with its status of either `unassigned` or `assigned`, and the customer name, address, and region of the customer location it was generated from
