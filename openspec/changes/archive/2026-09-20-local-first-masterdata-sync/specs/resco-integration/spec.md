# Spec Delta

## REMOVED Requirements

### Requirement: Customers and customer locations sync to Resco automatically after a Tripletex sync
**Reason**: this tied automatic Resco pushes to a Tripletex *pull* sync completing, which no longer exists in any automatic form (see `local-first-masterdata-sync`'s proposal - no Tripletex sync runs at startup, and the on-demand sync is now a push, not a pull). Customer and customer-location creation and update now trigger their own Resco push attempt directly, the same way employees and products already do.
**Migration**: See the new "Customers and customer locations sync to Resco automatically on create and update" requirement.

## ADDED Requirements

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
