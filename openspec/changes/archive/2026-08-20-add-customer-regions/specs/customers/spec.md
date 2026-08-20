## Purpose

Represents customers and the physical locations where they receive service; each location sits in a region and is what service visits are generated from.

## ADDED Requirements

### Requirement: Customer data model
The system SHALL persist each customer with a unique identifier and a name.

#### Scenario: Customer is persisted with required fields
- **WHEN** a customer record is created with id and name
- **THEN** the system persists the customer and both fields are retrievable unchanged

### Requirement: Customer location data model
The system SHALL persist each customer location with a unique identifier, the customer it belongs to, the region it is in, an address, and a geographic location (latitude, longitude).

#### Scenario: Customer location is persisted with required fields
- **WHEN** a customer location is created with id, customer_id, region_id, address, latitude, and longitude
- **THEN** the system persists the customer location and all fields are retrievable unchanged

### Requirement: A customer can have multiple locations
The system SHALL allow a customer to have one or more customer locations.

#### Scenario: Customer with multiple locations
- **WHEN** a customer has two or more customer locations persisted with its customer_id
- **THEN** each location is retrievable and associated with that customer
