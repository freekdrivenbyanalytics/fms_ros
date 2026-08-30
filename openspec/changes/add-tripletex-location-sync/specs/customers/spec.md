## ADDED Requirements

### Requirement: Customer locations are synced from Tripletex
The system SHALL fetch delivery addresses from Tripletex and reconcile them into the locally persisted customer locations: a Tripletex delivery address linked to a known local customer and not yet persisted locally SHALL be added, one already persisted locally SHALL have its fields updated to match Tripletex, and one no longer present in Tripletex SHALL be marked deleted (via a delete flag) rather than removed, leaving any contracts, service visits, and assignments that depend on it unaffected. A locally persisted customer location previously marked deleted that reappears in Tripletex SHALL have its deleted mark cleared and its fields overwritten to match Tripletex. A Tripletex delivery address with no linked customer SHALL be skipped.

#### Scenario: New Tripletex delivery address is added locally
- **WHEN** a sync runs and Tripletex includes a delivery address, linked to a known local customer, that is not yet persisted locally
- **THEN** the system creates a local customer location for it, associated with that customer

#### Scenario: Delivery address with no linked customer is skipped
- **WHEN** a sync runs and Tripletex includes a delivery address with no linked customer
- **THEN** the system does not create a customer location for it

#### Scenario: Changed Tripletex delivery address is updated locally
- **WHEN** a sync runs and a Tripletex delivery address's fields differ from the locally persisted customer location
- **THEN** the system updates the local record's fields to match Tripletex

#### Scenario: Removed Tripletex delivery address is marked deleted locally
- **WHEN** a sync runs and a locally persisted customer location is no longer present in Tripletex
- **THEN** the system marks that customer location as deleted, and its contracts, service visits, and assignments remain persisted and unaffected

#### Scenario: A previously deleted customer location reappears in Tripletex
- **WHEN** a sync runs and a locally persisted customer location that was marked deleted is present in Tripletex again
- **THEN** the system clears that customer location's deleted mark and updates its fields to match Tripletex

### Requirement: Deleted customer locations are hidden by default
The system SHALL exclude customer locations marked deleted from the customer location list returned to callers by default.

#### Scenario: Deleted customer location is excluded from the list
- **WHEN** a caller requests the list of customer locations
- **THEN** customer locations marked deleted are not included in the result

### Requirement: Customer location sync triggers
The system SHALL run the Tripletex customer location sync automatically each time the backend starts, and SHALL also support triggering it on demand using the same trigger as the customer sync. The backend SHALL remain able to start even when Tripletex is unreachable at startup.

#### Scenario: Sync runs on backend startup
- **WHEN** the backend starts and Tripletex is reachable
- **THEN** the system runs a Tripletex customer location sync before serving requests that depend on customer location data being current

#### Scenario: Sync can be triggered on demand
- **WHEN** a customer sync is triggered on demand
- **THEN** the system also runs the same customer location reconciliation

#### Scenario: Tripletex unreachable at startup does not block the backend
- **WHEN** the backend starts and Tripletex is unreachable
- **THEN** the backend still starts and serves requests, using whatever customer location data was already persisted locally

### Requirement: Sync does not assign a customer location's region
The system SHALL NOT set or change a customer location's region as part of syncing from Tripletex, since Tripletex has no equivalent concept. A customer location's region SHALL remain whatever it was previously assigned, or unset if it has never been assigned.

#### Scenario: Sync does not set a region for a new customer location
- **WHEN** a sync creates a new local customer location from a Tripletex delivery address
- **THEN** the system does not assign a region to it

#### Scenario: Sync does not change an existing customer location's region
- **WHEN** a sync updates an existing customer location's fields from Tripletex
- **THEN** the system does not modify that customer location's region

### Requirement: A customer location's coordinates are geocoded from its address
The system SHALL resolve a customer location's geographic coordinates by geocoding its address through an open-source geocoding service when the location is created or its address changes, and SHALL persist the resolved coordinates so unchanged addresses are not re-geocoded on a later sync. A customer location whose coordinates have not yet been resolved SHALL have no latitude/longitude.

#### Scenario: New customer location's coordinates are resolved
- **WHEN** a customer location is created with an address that can be geocoded
- **THEN** the system persists the resolved latitude and longitude for that location

#### Scenario: Geocoding does not repeat for an unchanged address
- **WHEN** a sync runs and a customer location's address is unchanged from the last sync
- **THEN** the system does not geocode that address again

### Requirement: Customer location changes are logged
The system SHALL record a log entry each time a sync creates a customer location, updates a customer location's fields, marks a customer location deleted, or restores a previously deleted customer location, capturing the customer location's id, the type of change, and when it occurred.

#### Scenario: Customer location creation is logged
- **WHEN** a sync creates a new local customer location
- **THEN** the system records a log entry for that customer location with change type "created"

#### Scenario: Customer location field update is logged
- **WHEN** a sync updates an existing local customer location's fields
- **THEN** the system records a log entry for that customer location with change type "updated"

#### Scenario: Customer location deletion is logged
- **WHEN** a sync marks a local customer location deleted
- **THEN** the system records a log entry for that customer location with change type "deleted"

#### Scenario: Customer location restoration is logged
- **WHEN** a sync clears a local customer location's deleted mark
- **THEN** the system records a log entry for that customer location with change type "restored"

## MODIFIED Requirements

### Requirement: Customer location data model
The system SHALL persist each customer location using Tripletex as the source of truth for its identity and address fields: each customer location's unique identifier SHALL be the id Tripletex assigns to its delivery address, and its address fields SHALL be set from the corresponding Tripletex delivery address record. The system SHALL additionally persist the customer it belongs to, the region it is in once assigned, and a geographic location (latitude, longitude) once resolved.

#### Scenario: Customer location is persisted with required fields
- **WHEN** a customer location is created with id, customer_id, region_id, address, latitude, and longitude
- **THEN** the system persists the customer location and all fields are retrievable unchanged
