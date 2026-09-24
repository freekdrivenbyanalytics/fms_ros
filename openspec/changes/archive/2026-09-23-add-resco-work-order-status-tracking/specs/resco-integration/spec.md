# Spec Delta

## MODIFIED Requirements

### Requirement: Assignments are synced to Resco as Work Orders
The system SHALL let assignment data be pushed to Resco by creating or updating a corresponding Work Order record in Resco, sending that assignment's planned start and end time, the assigned employee (as the Work Order's resource, via that employee's remembered Resco User ID), the visit's customer location (as the Work Order's linked asset, via that location's remembered Resco Asset ID), and the visit's parent customer (as the Work Order's required customer reference, via Customer.resco_account_id). The Work Order's name SHALL identify both the customer and the customer location ("Customer name: address | Visit <service_visit_id>"), so different locations and repeated visits are distinguishable. The visit suffix SHALL be retained within the 160-character name limit; names SHALL NOT be used as identity keys. A newly created Work Order SHALL end up in a scheduled state in Resco, not left in an incomplete/draft state, once its required fields and schedule are both present.

#### Scenario: A new assignment is created as a Work Order in Resco
- **WHEN** an assignment with no remembered Resco Work Order ID is synced
- **THEN** the system creates a new Work Order in Resco with that assignment's planned start and end time, resource, linked asset, and customer, and remembers the returned Resco Work Order ID against that assignment

#### Scenario: A reassigned assignment's Work Order in Resco is updated
- **WHEN** an assignment with a remembered Resco Work Order ID is synced after its employee or planned time has changed
- **THEN** the system updates that Resco Work Order's resource and/or planned start and end time rather than creating a new one

#### Scenario: A newly synced Work Order is scheduled, not draft
- **WHEN** an assignment is synced to Resco for the first time, creating its Work Order and schedule
- **THEN** the resulting Work Order does not remain in an incomplete/draft state in Resco - it has every field Resco requires to be considered scheduled

### Requirement: Customer locations are synced to Resco as Assets
The system SHALL let customer location data be pushed to Resco by creating or updating a corresponding Asset record in Resco, using exactly the same name as its Resco functional location and linking it to both that functional location and its parent customer's Resco Account. The functional location SHALL be synced first; each portal location SHALL have its own Asset, reused on subsequent syncs. Both names SHALL use the portal location's address, the existing location display name.

#### Scenario: A new customer location is created as an Asset in Resco
- **WHEN** a customer location with no remembered Resco Asset ID is synced, and its customer has a remembered Resco Account ID
- **THEN** the system creates a new Asset in Resco with the same name as the location's functional location, linked to that functional location and the customer's Resco Account, and remembers the returned Resco Asset ID against that location

#### Scenario: An existing customer location's Asset in Resco is updated
- **WHEN** a customer location with a remembered Resco Asset ID is synced
- **THEN** the system updates that Asset's name and links using its remembered ID, keeping its name equal to the functional location name rather than creating a new one

#### Scenario: A customer location whose customer isn't yet synced is skipped
- **WHEN** a customer location is synced and its customer has no remembered Resco Account ID
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations — it becomes eligible again once its customer is synced

#### Scenario: A customer location with no street address is skipped
- **WHEN** a customer location with no street address is synced
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations

### Requirement: Customers and customer locations sync to Resco automatically on create and update
The system SHALL attempt to sync a customer to Resco immediately after that customer is created or updated, and a customer location to Resco immediately after that location is created or updated. A failure of this automatic sync (Resco unreachable, an error response, or a missing required dependency) SHALL NOT fail or roll back the customer or customer-location create or update itself.

#### Scenario: Creating a customer triggers a Resco sync attempt
- **WHEN** a user creates a customer
- **THEN** the system attempts to sync that customer to Resco after it is persisted, and the customer is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a customer triggers a Resco sync attempt
- **WHEN** a user updates a customer
- **THEN** the system attempts to sync that customer to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

#### Scenario: Creating a customer location triggers a Resco sync attempt
- **WHEN** a user creates a customer location
- **THEN** the system attempts to sync that location to Resco after it is persisted, and the location is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a customer location triggers a Resco sync attempt
- **WHEN** a user updates a customer location
- **THEN** the system attempts to sync that location to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

### Requirement: A user can manually trigger syncing all customers or all customer locations to Resco
The system SHALL let a user trigger a sync of every non-deleted customer to Resco on demand, and separately a sync of every non-deleted customer location to Resco on demand, each returning a summary of how many were created, updated, skipped, and failed.

#### Scenario: Manually syncing all customers
- **WHEN** a user triggers a manual customer sync to Resco
- **THEN** the system attempts to sync every non-deleted customer to Resco and returns a summary counting how many were created, updated, and failed

#### Scenario: Manually syncing all customer locations
- **WHEN** a user triggers a manual customer location sync to Resco
- **THEN** the system attempts to sync every non-deleted customer location to Resco and returns a summary counting how many were created, updated, skipped (customer not yet synced, or the location has no street address), and failed

### Requirement: An assignment whose employee or location isn't yet synced to Resco is skipped, not failed
The system SHALL require the assignment's employee to have a remembered Resco User ID and the visit's customer location to have both a remembered Resco functional location ID and a remembered Resco Asset ID, with its parent customer having a remembered Resco Account ID to sync an assignment to Resco. An assignment missing either SHALL be skipped for that sync, reported as skipped, and SHALL NOT prevent the assignment itself from being created, or other assignments in the same batch from being synced.

#### Scenario: An assignment whose employee isn't yet synced to Resco is skipped
- **WHEN** an assignment is synced whose employee has no remembered Resco User ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and the assignment is still created

#### Scenario: An assignment whose customer location isn't yet synced to Resco is skipped
- **WHEN** an assignment is synced whose visit's customer location lacks its functional location or Asset ID, or its parent customer lacks an Account ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and the assignment is still created

#### Scenario: One assignment's Resco failure does not block others in the same apply
- **WHEN** applying a proposed schedule creates or updates multiple assignments and Resco returns an error for one of them
- **THEN** the system reports that assignment's sync as failed and still attempts every other assignment's sync in the same apply

### Requirement: Customers are synced to Resco as Accounts
The system SHALL let customer data be pushed to Resco by creating or updating a corresponding Account record in Resco, sending that customer's name, email, phone, organization/VAT number, and address. Each portal customer SHALL map to one Account, named after the customer, regardless of its number of locations. Contact-person name and mobile SHALL also be synced when present, with exact Resco mappings verified before implementation. Changes and explicit clears SHALL update that same Account using Customer.resco_account_id. Customer updates SHALL NOT replace location-specific functional-location addresses or coordinates.

#### Scenario: A new customer is created as an Account in Resco
- **WHEN** a customer with no remembered Resco Account ID is synced
- **THEN** the system creates a new Account in Resco with that customer's name, email, phone, organization number, and address, and remembers the returned Resco Account ID against that customer

#### Scenario: An existing customer's Account in Resco is updated
- **WHEN** a customer with a remembered Resco Account ID is synced
- **THEN** the system updates that Resco Account's name, email, phone, organization number, and address rather than creating a new one

## ADDED Requirements



### Requirement: An assignment's Resco Work Order status can be pulled on demand
The system SHALL let a user trigger, on demand only (no automatic or scheduled job), a bulk pull of the current Resco Work Order status for every assignment with a remembered Resco Work Order ID, storing each one's latest status locally. An assignment with no remembered Resco Work Order ID SHALL be skipped, reported as skipped, and SHALL NOT prevent the pull from continuing to the remaining assignments. A failure pulling one assignment's status SHALL NOT prevent the pull from continuing to the remaining assignments.

#### Scenario: Pulling status updates the locally stored value
- **WHEN** a user triggers a status pull and an assignment has a remembered Resco Work Order ID
- **THEN** the system fetches that Work Order's current status from Resco and stores it against the assignment, replacing whatever was previously stored

#### Scenario: An assignment never synced to Resco is skipped
- **WHEN** a user triggers a status pull and an assignment has no remembered Resco Work Order ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and continues with the remaining assignments

#### Scenario: One assignment's pull failure does not block the rest
- **WHEN** a status pull processes multiple assignments and fetching one fails
- **THEN** the system continues pulling status for the remaining assignments and reports the failure for that one

#### Scenario: The status pull only runs on demand
- **WHEN** the backend starts, or at any other automatic trigger point
- **THEN** no Resco Work Order status pull runs automatically; it only runs when a user explicitly triggers it

### Requirement: Eligible overdue reconciliation resets the Work Order to Draft
The system SHALL attempt to reset the existing Work Order to Draft (statecode 0, statuscode 1) when portal reconciliation unassigns a past planned assignment whose previously synced Work Order is currently Scheduled. It SHALL NOT reset other statuses or reset Work Orders on ordinary manual unassignment. A failed reset SHALL NOT roll back local unassignment; the system SHALL report the failure and preserve the remote identity and reset context for retry independently of the deleted assignment. A retry SHALL recheck eligibility and SHALL NOT overwrite subsequent field progress.

#### Scenario: Eligible work is returned to Draft
- **WHEN** reconciliation unassigns an eligible past Scheduled assignment
- **THEN** the portal attempts to set that same Work Order to Draft without deleting it

#### Scenario: Remote reset fails
- **WHEN** Resco rejects or cannot receive the Draft reset
- **THEN** the visit remains unassigned locally, the failure is reported, and reset context remains available for retry

#### Scenario: Ordinary manual unassignment leaves Resco untouched
- **WHEN** a user manually unassigns a visit outside overdue reconciliation
- **THEN** this change does not trigger a remote status reset






### Requirement: Customer locations are synced to Resco as functional locations
The system SHALL create or update one Resco functional location per portal customer-location, named using the location's address (its existing portal display name), sending its address fields and optional latitude/longitude. It SHALL remember the returned technical ID on CustomerLocation.resco_functional_location_id and reuse it for updates. Each functional location SHALL have one portal-managed Asset with exactly the same name, linked through resco_functionallocationid_resco_functionallocation and to the parent customer Account through customerid_account. A location SHALL NOT create its own Resco Account. Equal names SHALL NOT merge distinct portal locations; remembered technical IDs determine identity.

#### Scenario: A customer has two locations
- **WHEN** one customer with two locations is synced
- **THEN** Resco has one customer Account, two functional locations with their respective addresses and coordinates, and one same-named Asset under each functional location, both Assets linked to that Account

#### Scenario: Coordinates are missing or added later
- **WHEN** a location without coordinates is synced and later receives coordinates
- **THEN** its functional location and Asset can be created without coordinates and the next sync updates the same functional location with the resolved coordinates

#### Scenario: An existing location changes
- **WHEN** a location address or coordinates change
- **THEN** sync updates the existing functional location and keeps its Asset name equal to the functional location name without changing other locations

#### Scenario: Functional location creation succeeds but Asset creation fails
- **WHEN** the functional location is created but the subsequent Asset operation fails
- **THEN** its technical ID remains saved for retry and the retry creates no duplicate functional location

#### Scenario: Existing Assets acquire functional locations
- **WHEN** a portal location already has a remembered Asset but no functional location ID
- **THEN** sync creates and remembers its functional location, updates the existing Asset's name and functional-location link, and retains the parent customer Account

### Requirement: Work Orders use the Asset of the visit's functional location
The system SHALL bind an assigned visit's Work Order to the Asset remembered on that visit's portal customer-location, which SHALL link to that same location's Resco functional location. The Work Order's customer SHALL be the parent customer's Resco Account. It SHALL NOT choose an arbitrary Asset belonging to the customer or create a location-specific Account. Missing dependencies SHALL skip the remote Work Order sync with an explanation without failing the local assignment.

#### Scenario: Visits at different locations of one customer
- **WHEN** two assigned visits for different locations of the same customer are synced
- **THEN** both Work Orders reference the same Account and each references the Asset belonging to its own functional location

### Requirement: Customer contact updates remain shared across locations
The system SHALL update the parent customer's single Resco Account with name, organization number, contact-person name, email, telephone and mobile, including explicit clears. It SHALL reuse existing portal fields and add missing editing support. Resco Account or linked Contact field mappings SHALL be verified before implementation. Every location's Asset SHALL remain linked to this Account so customer contact masterdata is shared rather than copied into location Accounts. Remote failures SHALL be reported and retryable without rolling back the local customer write.

#### Scenario: Contact information changes for a customer with multiple locations
- **WHEN** a customer contact value changes or is cleared
- **THEN** sync updates the same parent Account, all location Assets retain that Account link, and each functional location keeps its own address and coordinates

## REMOVED Requirements



### Requirement: Unassigning a visit does not affect its Resco Work Order
**Reason**: The user requests a Draft reset for past Work Orders that is currently Scheduled.
**Migration**: Apply the narrowly scoped reconciliation reset below; ordinary manual unassignment retains its existing behavior.
