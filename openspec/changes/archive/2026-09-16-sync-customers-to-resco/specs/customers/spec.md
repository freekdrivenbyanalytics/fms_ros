## MODIFIED Requirements

### Requirement: Customer data model
The system SHALL persist each customer using Tripletex as the source of truth: each customer's unique identifier SHALL be the id Tripletex assigns to it, and the customer's fields SHALL be set from the corresponding Tripletex customer record. The system SHALL additionally persist a remembered Resco Account ID once the customer has been synced to Resco.

#### Scenario: Customer is persisted with required fields
- **WHEN** a customer record is created from a Tripletex customer
- **THEN** the system persists the customer using that Tripletex customer's id as its unique identifier, with its fields set from the corresponding Tripletex customer's fields, and both the identifier and fields are retrievable unchanged

### Requirement: Customer location data model
The system SHALL persist each customer location using Tripletex as the source of truth for its identity and address fields: each customer location's unique identifier SHALL be the id Tripletex assigns to its delivery address, and its address fields SHALL be set from the corresponding Tripletex delivery address record. The system SHALL additionally persist the customer it belongs to, the region it is in once assigned, a geographic location (latitude, longitude) once resolved, whether its coordinates are locked against being overwritten by a future sync's geocoding step, and a remembered Resco Asset ID once the location has been synced to Resco.

#### Scenario: Customer location is persisted with required fields
- **WHEN** a customer location is created with id, customer_id, region_id, address, latitude, and longitude
- **THEN** the system persists the customer location and all fields are retrievable unchanged

#### Scenario: A customer location's coordinates are not locked by default
- **WHEN** a customer location is created
- **THEN** its coordinates are not locked, so a sync's geocoding step may resolve or update them normally
