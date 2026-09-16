## ADDED Requirements

### Requirement: Products are synced to Resco
The system SHALL let product data be pushed to Resco by creating or updating a corresponding Product record in Resco, sending that product's name and product number.

#### Scenario: A new product is created in Resco
- **WHEN** a product with no remembered Resco Product ID is synced
- **THEN** the system creates a new Product in Resco with that product's name and number, and remembers the returned Resco Product ID against that product

#### Scenario: An existing product's Resco record is updated
- **WHEN** a product with a remembered Resco Product ID is synced
- **THEN** the system updates that Resco Product's name and number rather than creating a new one

### Requirement: Products sync to Resco on create and update
The system SHALL attempt to sync a product to Resco immediately after that product is created or updated in fms_ros. A failure of this automatic sync SHALL NOT fail or roll back the product create or update itself.

#### Scenario: Creating a product triggers a sync attempt
- **WHEN** a user creates a product in fms_ros
- **THEN** the system attempts to sync that product to Resco after it is persisted, and the product is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a product triggers a sync attempt
- **WHEN** a user updates a product in fms_ros
- **THEN** the system attempts to sync that product to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds
