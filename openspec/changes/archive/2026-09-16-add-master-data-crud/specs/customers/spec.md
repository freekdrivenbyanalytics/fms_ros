## MODIFIED Requirements

### Requirement: Customer data model
The system SHALL persist each customer using Tripletex as the system of record: each customer's unique identifier SHALL be the id Tripletex assigns to it, and the customer's fields SHALL be kept in sync with the corresponding Tripletex customer record, whether that customer was originally created in Tripletex or in fms_ros. The system SHALL additionally persist a remembered Resco Account ID once the customer has been synced to Resco.

#### Scenario: Customer is persisted with required fields
- **WHEN** a customer record is created from a Tripletex customer
- **THEN** the system persists the customer using that Tripletex customer's id as its unique identifier, with its fields set from the corresponding Tripletex customer's fields, and both the identifier and fields are retrievable unchanged

### Requirement: Customer location data model
The system SHALL persist each customer location using Tripletex as the system of record for its identity and address fields: each customer location's unique identifier SHALL be the id Tripletex assigns to its delivery address, and its address fields SHALL be kept in sync with the corresponding Tripletex delivery address record, whether that location was originally created in Tripletex or in fms_ros. The system SHALL additionally persist the customer it belongs to, the region it is in once assigned, a geographic location (latitude, longitude) once resolved, whether its coordinates are locked against being overwritten by a future sync's geocoding step, and a remembered Resco Asset ID once the location has been synced to Resco.

#### Scenario: Customer location is persisted with required fields
- **WHEN** a customer location is created with id, customer_id, region_id, address, latitude, and longitude
- **THEN** the system persists the customer location and all fields are retrievable unchanged

#### Scenario: A customer location's coordinates are not locked by default
- **WHEN** a customer location is created
- **THEN** its coordinates are not locked, so a sync's geocoding step may resolve or update them normally

## ADDED Requirements

### Requirement: Create, update, and soft-delete a customer
The system SHALL allow a user to create a customer with a name, which the system SHALL push to Tripletex as a new customer, adopting Tripletex's returned id as the new customer's own id; update a customer's fields, which the system SHALL push to Tripletex as an update to the corresponding Tripletex customer; and soft-delete a customer. A soft-deleted customer SHALL NOT be permanently removed, and SHALL NOT be deleted from Tripletex. Creating a customer does not create a customer location — a new customer starts with none, and locations are added separately.

#### Scenario: Creating a customer
- **WHEN** a user creates a customer with a name
- **THEN** the system creates the corresponding customer in Tripletex, persists a local customer using the id Tripletex returns, and that customer is retrievable with the name the user provided, with no customer locations yet

#### Scenario: Updating a customer
- **WHEN** a user updates a customer's fields
- **THEN** the system persists the change locally and pushes the same change to the corresponding Tripletex customer

#### Scenario: Soft-deleting a customer
- **WHEN** a user soft-deletes a customer
- **THEN** the system marks it deleted locally rather than removing it, and does not delete or otherwise modify the corresponding record in Tripletex

#### Scenario: A soft-deleted customer stays excluded after a later Tripletex sync
- **WHEN** a customer is soft-deleted in fms_ros, and a later Tripletex sync runs while that customer is still present and unchanged in Tripletex
- **THEN** the customer remains excluded from the customer list — the sync SHALL NOT treat its continued presence in Tripletex as a reason to undo the local soft-delete

### Requirement: Create, update, and soft-delete a customer location
The system SHALL allow a user to create a customer location for an existing customer with an address, which the system SHALL push to Tripletex as a new delivery address for that customer, adopting Tripletex's returned id as the new location's own id; update a customer location's address, which the system SHALL push to Tripletex as an update to the corresponding delivery address; and soft-delete a customer location. A soft-deleted customer location SHALL NOT be permanently removed, and SHALL NOT be deleted from Tripletex (which has no delete operation for a delivery address).

#### Scenario: Creating a customer location
- **WHEN** a user creates a customer location for an existing customer with an address
- **THEN** the system creates the corresponding delivery address in Tripletex linked to that customer, persists a local customer location using the id Tripletex returns, and that location is retrievable with the address the user provided

#### Scenario: Updating a customer location
- **WHEN** a user updates a customer location's address
- **THEN** the system persists the change locally and pushes the same change to the corresponding Tripletex delivery address

#### Scenario: Soft-deleting a customer location
- **WHEN** a user soft-deletes a customer location
- **THEN** the system marks it deleted locally rather than removing it, and does not attempt to delete the corresponding delivery address in Tripletex

#### Scenario: A soft-deleted customer location stays excluded after a later Tripletex sync
- **WHEN** a customer location is soft-deleted in fms_ros, and a later Tripletex sync runs while that location is still present and unchanged in Tripletex
- **THEN** the location remains excluded from the customer location list — the sync SHALL NOT treat its continued presence in Tripletex as a reason to undo the local soft-delete
