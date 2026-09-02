## MODIFIED Requirements

### Requirement: Customer location data model
The system SHALL persist each customer location using Tripletex as the source of truth for its identity and address fields: each customer location's unique identifier SHALL be the id Tripletex assigns to its delivery address, and its address fields SHALL be set from the corresponding Tripletex delivery address record. The system SHALL additionally persist the customer it belongs to, the region it is in once assigned, a geographic location (latitude, longitude) once resolved, and whether its coordinates are locked against being overwritten by a future sync's geocoding step.

#### Scenario: Customer location is persisted with required fields
- **WHEN** a customer location is created with id, customer_id, region_id, address, latitude, and longitude
- **THEN** the system persists the customer location and all fields are retrievable unchanged

#### Scenario: A customer location's coordinates are not locked by default
- **WHEN** a customer location is created
- **THEN** its coordinates are not locked, so a sync's geocoding step may resolve or update them normally

### Requirement: A customer location's coordinates are geocoded from its address
The system SHALL resolve a customer location's geographic coordinates by geocoding its address through an open-source geocoding service when the location is created or its address changes, and SHALL persist the resolved coordinates so unchanged addresses are not re-geocoded on a later sync. A customer location whose coordinates have not yet been resolved SHALL have no latitude/longitude. Geocoding SHALL be skipped entirely for a customer location whose coordinates are locked, regardless of whether its address changed.

#### Scenario: New customer location's coordinates are resolved
- **WHEN** a customer location is created with an address that can be geocoded
- **THEN** the system persists the resolved latitude and longitude for that location

#### Scenario: Geocoding does not repeat for an unchanged address
- **WHEN** a sync runs and a customer location's address is unchanged from the last sync
- **THEN** the system does not geocode that address again

#### Scenario: Geocoding is skipped for a locked customer location
- **WHEN** a sync runs and a customer location's coordinates are locked, even if its address changed
- **THEN** the system does not geocode that location's address, and its existing coordinates are left unchanged
