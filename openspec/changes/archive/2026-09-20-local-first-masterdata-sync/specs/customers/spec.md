# Spec Delta

## MODIFIED Requirements

### Requirement: Customer data model
The system SHALL persist each customer using fms_ros as the system of record for its identity: each customer's unique identifier SHALL be an id assigned by fms_ros, not by Tripletex, whether or not that customer has ever been synced to Tripletex. The system SHALL additionally persist a remembered Tripletex customer id once the customer has been synced to Tripletex, and a remembered Resco Account ID once the customer has been synced to Resco.

#### Scenario: Customer is persisted with required fields
- **WHEN** a customer record is created
- **THEN** the system persists the customer using an id assigned by fms_ros as its unique identifier, with its fields retrievable unchanged, and no Tripletex id remembered until the customer has been synced to Tripletex

### Requirement: Customer location data model
The system SHALL persist each customer location using fms_ros as the system of record for its identity: each customer location's unique identifier SHALL be an id assigned by fms_ros, not by Tripletex, whether or not that location has ever been synced to Tripletex. The system SHALL additionally persist the customer it belongs to, the region it is in once assigned, a geographic location (latitude, longitude) once resolved, whether its coordinates are locked against being overwritten by a future geocoding step, a remembered Tripletex delivery address id once the location has been synced to Tripletex, and a remembered Resco Asset ID once the location has been synced to Resco.

#### Scenario: Customer location is persisted with required fields
- **WHEN** a customer location is created with customer_id, address, latitude, and longitude
- **THEN** the system persists the customer location using an id assigned by fms_ros, and all fields are retrievable unchanged, with no Tripletex id remembered until the location has been synced to Tripletex

#### Scenario: A customer location's coordinates are not locked by default
- **WHEN** a customer location is created
- **THEN** its coordinates are not locked, so a future geocoding step may resolve or update them normally

### Requirement: Create, update, and soft-delete a customer
The system SHALL allow a user to create a customer with a name: the system SHALL persist the customer locally first, assigning it an fms_ros id, and SHALL then attempt to push it to Tripletex as a new customer and to Resco as a new Account, remembering whichever ids are returned. A push failure to either system SHALL NOT fail the create; the create response SHALL include a warning identifying which system(s) the push failed for and stating that the sync needs to be retried. The system SHALL allow a user to update a customer's fields, persisting the change locally first and then attempting to push the same change to the corresponding Tripletex customer (if the customer has a remembered Tripletex id) and Resco Account (if it has a remembered Resco id); a push failure SHALL NOT fail the update, and the update response SHALL include the same kind of warning. The system SHALL allow a user to soft-delete a customer. A soft-deleted customer SHALL NOT be permanently removed, and SHALL NOT be deleted from Tripletex. Creating a customer does not create a customer location — a new customer starts with none, and locations are added separately.

#### Scenario: Creating a customer
- **WHEN** a user creates a customer with a name
- **THEN** the system persists a local customer with an fms_ros-assigned id and the name the user provided, with no customer locations yet, and attempts to push it to Tripletex and Resco

#### Scenario: Creating a customer when Tripletex and/or Resco is unreachable
- **WHEN** a user creates a customer while Tripletex and/or Resco cannot be reached or returns an error
- **THEN** the customer is still persisted locally with an fms_ros-assigned id, and the create response includes a warning naming the system(s) the sync failed for

#### Scenario: Updating a customer
- **WHEN** a user updates a customer's fields
- **THEN** the system persists the change locally and attempts to push the same change to the corresponding Tripletex customer and Resco Account, for whichever of those the customer has a remembered id for

#### Scenario: Updating a customer when the push fails
- **WHEN** a user updates a customer's fields and the push to Tripletex and/or Resco fails
- **THEN** the local update still succeeds, and the update response includes a warning naming the system(s) the sync failed for

#### Scenario: Soft-deleting a customer
- **WHEN** a user soft-deletes a customer
- **THEN** the system marks it deleted locally rather than removing it, and does not delete or otherwise modify the corresponding record in Tripletex

#### Scenario: A soft-deleted customer stays excluded after a later Tripletex sync
- **WHEN** a customer is soft-deleted in fms_ros, and a later Tripletex/Resco bootstrap sync runs
- **THEN** that customer is excluded from the bootstrap sync's candidates, and its corresponding Tripletex/Resco record (if any) is left unmodified

### Requirement: Create, update, and soft-delete a customer location
The system SHALL allow a user to create a customer location for an existing customer with an address: the system SHALL persist the location locally first, assigning it an fms_ros id, and SHALL then attempt to push it to Tripletex as a new delivery address for that customer and to Resco as a new Asset, remembering whichever ids are returned. A push failure to either system SHALL NOT fail the create; the create response SHALL include a warning identifying which system(s) the push failed for and stating that the sync needs to be retried. The system SHALL allow a user to update a customer location's address, persisting the change locally first and then attempting to push the same change to the corresponding Tripletex delivery address (if the location has a remembered Tripletex id) and Resco Asset (if it has a remembered Resco id); a push failure SHALL NOT fail the update, and the update response SHALL include the same kind of warning. The system SHALL allow a user to soft-delete a customer location. A soft-deleted customer location SHALL NOT be permanently removed, and SHALL NOT be deleted from Tripletex (which has no delete operation for a delivery address).

#### Scenario: Creating a customer location
- **WHEN** a user creates a customer location for an existing customer with an address
- **THEN** the system persists a local customer location with an fms_ros-assigned id and the address the user provided, and attempts to push it to Tripletex and Resco

#### Scenario: Creating a customer location when Tripletex and/or Resco is unreachable
- **WHEN** a user creates a customer location while Tripletex and/or Resco cannot be reached or returns an error
- **THEN** the location is still persisted locally with an fms_ros-assigned id, and the create response includes a warning naming the system(s) the sync failed for

#### Scenario: Updating a customer location
- **WHEN** a user updates a customer location's address
- **THEN** the system persists the change locally and attempts to push the same change to the corresponding Tripletex delivery address and Resco Asset, for whichever of those the location has a remembered id for

#### Scenario: Updating a customer location when the push fails
- **WHEN** a user updates a customer location's address and the push to Tripletex and/or Resco fails
- **THEN** the local update still succeeds, and the update response includes a warning naming the system(s) the sync failed for

#### Scenario: Soft-deleting a customer location
- **WHEN** a user soft-deletes a customer location
- **THEN** the system marks it deleted locally rather than removing it, and does not attempt to delete the corresponding delivery address in Tripletex

#### Scenario: A soft-deleted customer location stays excluded after a later Tripletex sync
- **WHEN** a customer location is soft-deleted in fms_ros, and a later Tripletex/Resco bootstrap sync runs
- **THEN** that location is excluded from the bootstrap sync's candidates, and its corresponding Tripletex/Resco record (if any) is left unmodified

## REMOVED Requirements

### Requirement: Customers are synced from Tripletex
**Reason**: fms_ros is now the system of record for customers; Tripletex no longer originates new customers this system needs to discover, so pulling Tripletex's customer list into fms_ros (creating local records for ones fms_ros doesn't have, overwriting local fields with Tripletex's) no longer fits the ownership model.
**Migration**: See the new "Customers are bootstrap-synced to Tripletex and Resco" requirement - it pushes fms_ros's own data outward instead of pulling Tripletex's data in.

### Requirement: Customer sync triggers
**Reason**: paired with the removed pull-sync requirement above; startup no longer runs any Tripletex sync at all (see this change's proposal), and the on-demand trigger's behavior is superseded by the new bootstrap-push trigger.
**Migration**: See "Customers are bootstrap-synced to Tripletex and Resco" for the (on-demand only, push-based) replacement trigger.

### Requirement: Customer location sync triggers
**Reason**: same as "Customer sync triggers" above, for customer locations.
**Migration**: See the new "Customer locations are bootstrap-synced to Tripletex and Resco" requirement.

### Requirement: Sync does not assign a customer location's region
**Reason**: this requirement protected a customer location's region from being overwritten by an incoming pull from Tripletex. There is no longer any incoming pull that touches local fields at all - the bootstrap sync only ever reads local data to push outward, never writes region or any other local field - so the concern this requirement guarded against no longer exists.
**Migration**: Not applicable. A customer location's region remains an exclusively local, portal-managed field.

### Requirement: Customer changes are logged
**Reason**: this logged the pull-sync's create/update/delete/restore actions specifically. The pull-sync no longer exists, and delete/restore no longer apply to how a customer's Tripletex link changes (see "Sync does not assign a customer location's region" reasoning - there is no more incoming reconciliation to log).
**Migration**: See "Customers are bootstrap-synced to Tripletex and Resco" - it logs its own create/update actions.

### Requirement: Customer location changes are logged
**Reason**: same as "Customer changes are logged" above, for customer locations.
**Migration**: See "Customer locations are bootstrap-synced to Tripletex and Resco".

## ADDED Requirements

### Requirement: Customers are bootstrap-synced to Tripletex and Resco
The system SHALL let a user trigger, on demand only (never automatically at backend startup), a bootstrap sync of every non-deleted, non-archived customer: for each such customer with no remembered Tripletex id, the system SHALL create a corresponding customer in Tripletex and remember the returned id; for each with no remembered Resco Account id, the system SHALL create a corresponding Account in Resco and remember the returned id; for each customer that already has a remembered Tripletex id and/or Resco Account id, the system SHALL instead push that customer's current local field values as an update to the corresponding Tripletex customer and/or Resco Account. The system SHALL record a log entry each time this sync creates or updates a customer's Tripletex or Resco link, capturing the customer's id, which system was affected, whether it was a create or an update, and when it occurred. A failure syncing one customer SHALL NOT prevent the sync from continuing to the remaining customers.

#### Scenario: A customer missing a Tripletex id is created in Tripletex
- **WHEN** a bootstrap sync runs and a local customer has no remembered Tripletex id
- **THEN** the system creates a corresponding customer in Tripletex using that customer's current local field values, and remembers the returned Tripletex id

#### Scenario: A customer with a remembered Tripletex id is updated in Tripletex
- **WHEN** a bootstrap sync runs and a local customer already has a remembered Tripletex id
- **THEN** the system pushes that customer's current local field values as an update to the corresponding Tripletex customer, rather than creating a new one

#### Scenario: A customer missing a Resco Account id is created in Resco
- **WHEN** a bootstrap sync runs and a local customer has no remembered Resco Account id
- **THEN** the system creates a corresponding Account in Resco, and remembers the returned Resco Account id

#### Scenario: One customer's sync failure does not block the rest
- **WHEN** a bootstrap sync processes multiple customers and one push fails
- **THEN** the system continues syncing the remaining customers and reports the failure for that one

#### Scenario: The bootstrap sync only runs on demand
- **WHEN** the backend starts
- **THEN** no customer bootstrap sync runs automatically; it only runs when a user explicitly triggers it

### Requirement: Customer locations are bootstrap-synced to Tripletex and Resco
The system SHALL let a user trigger, on demand only (never automatically at backend startup), a bootstrap sync of every non-deleted, non-archived customer location: for each such location with no remembered Tripletex id, the system SHALL create a corresponding delivery address in Tripletex (linked to its customer's remembered Tripletex id, when the customer has one) and remember the returned id; for each with no remembered Resco Asset id, the system SHALL create a corresponding Asset in Resco (linked to its customer's remembered Resco Account id, when the customer has one) and remember the returned id; for each location that already has a remembered Tripletex id and/or Resco Asset id, the system SHALL instead push that location's current local address to the corresponding Tripletex delivery address and/or Resco Asset. A location whose customer has no remembered Tripletex (respectively Resco) id yet SHALL be skipped for that system, reported as skipped, and SHALL become eligible again once its customer is synced. The system SHALL record a log entry each time this sync creates or updates a customer location's Tripletex or Resco link. A failure syncing one location SHALL NOT prevent the sync from continuing to the remaining locations.

#### Scenario: A location missing a Tripletex id is created in Tripletex
- **WHEN** a bootstrap sync runs, a local customer location has no remembered Tripletex id, and its customer has a remembered Tripletex id
- **THEN** the system creates a corresponding delivery address in Tripletex linked to that customer, and remembers the returned id

#### Scenario: A location with a remembered Tripletex id is updated in Tripletex
- **WHEN** a bootstrap sync runs and a local customer location already has a remembered Tripletex id
- **THEN** the system pushes that location's current local address as an update to the corresponding Tripletex delivery address, rather than creating a new one

#### Scenario: A location whose customer isn't yet synced to Tripletex is skipped
- **WHEN** a bootstrap sync runs and a local customer location's customer has no remembered Tripletex id
- **THEN** the system does not call Tripletex for that location, reports it as skipped, and continues with the remaining locations

#### Scenario: The bootstrap sync only runs on demand
- **WHEN** the backend starts
- **THEN** no customer location bootstrap sync runs automatically; it only runs when a user explicitly triggers it
