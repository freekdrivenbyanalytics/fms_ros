## ADDED Requirements

### Requirement: Customers are synced to Resco as Accounts
The system SHALL let customer data be pushed to Resco by creating or updating a corresponding Account record in Resco, sending that customer's name, email, phone, organization/VAT number, and address.

#### Scenario: A new customer is created as an Account in Resco
- **WHEN** a customer with no remembered Resco Account ID is synced
- **THEN** the system creates a new Account in Resco with that customer's name, email, phone, organization number, and address, and remembers the returned Resco Account ID against that customer

#### Scenario: An existing customer's Account in Resco is updated
- **WHEN** a customer with a remembered Resco Account ID is synced
- **THEN** the system updates that Resco Account's name, email, phone, organization number, and address rather than creating a new one

### Requirement: Customer locations are synced to Resco as Assets
The system SHALL let customer location data be pushed to Resco by creating or updating a corresponding Asset record in Resco, sending that location's address as the Asset's name and linking it to its customer's Resco Account.

#### Scenario: A new customer location is created as an Asset in Resco
- **WHEN** a customer location with no remembered Resco Asset ID is synced, and its customer has a remembered Resco Account ID
- **THEN** the system creates a new Asset in Resco with that location's address as its name, linked to the customer's Resco Account, and remembers the returned Resco Asset ID against that location

#### Scenario: An existing customer location's Asset in Resco is updated
- **WHEN** a customer location with a remembered Resco Asset ID is synced
- **THEN** the system updates that Resco Asset's name rather than creating a new one

#### Scenario: A customer location whose customer isn't yet synced is skipped
- **WHEN** a customer location is synced and its customer has no remembered Resco Account ID
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations — it becomes eligible again once its customer is synced

#### Scenario: A customer location with no street address is skipped
- **WHEN** a customer location with no street address is synced
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations

### Requirement: Customers and customer locations sync to Resco automatically after a Tripletex sync
The system SHALL attempt to sync every customer to Resco immediately after a Tripletex customer sync completes, and every customer location to Resco immediately after a Tripletex customer location sync completes. A failure of this automatic sync SHALL NOT fail or roll back the Tripletex sync itself.

#### Scenario: A Tripletex customer sync triggers a Resco sync attempt
- **WHEN** a Tripletex customer sync completes (at backend startup or on demand)
- **THEN** the system attempts to sync every customer to Resco afterward, and the Tripletex sync's own result is unaffected by whether that attempt succeeds

#### Scenario: A Tripletex customer location sync triggers a Resco sync attempt
- **WHEN** a Tripletex customer location sync completes (at backend startup or on demand)
- **THEN** the system attempts to sync every customer location to Resco afterward, and the Tripletex sync's own result is unaffected by whether that attempt succeeds

### Requirement: A user can manually trigger syncing all customers or all customer locations to Resco
The system SHALL let a user trigger a sync of every non-deleted customer to Resco on demand, and separately a sync of every non-deleted customer location to Resco on demand, each returning a summary of how many were created, updated, skipped, and failed.

#### Scenario: Manually syncing all customers
- **WHEN** a user triggers a manual customer sync to Resco
- **THEN** the system attempts to sync every non-deleted customer to Resco and returns a summary counting how many were created, updated, and failed

#### Scenario: Manually syncing all customer locations
- **WHEN** a user triggers a manual customer location sync to Resco
- **THEN** the system attempts to sync every non-deleted customer location to Resco and returns a summary counting how many were created, updated, skipped (customer not yet synced, or the location has no street address), and failed
