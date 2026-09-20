# Spec Delta

## MODIFIED Requirements

### Requirement: Product data model
The system SHALL persist each product with a unique identifier assigned by fms_ros (not by Tripletex), a product number, a product type (`TJN` for tjeneste/service or `PRD` for produkt/product — derived from the product number's prefix), a product name, a soft-delete flag, a remembered Tripletex product id once the product has been synced to Tripletex, and a remembered Resco Product ID once the product has been synced to Resco.

#### Scenario: Product is persisted with required fields
- **WHEN** a product record is created with a number and a name
- **THEN** the system persists the product using an fms_ros-assigned id, and all fields are retrievable unchanged, with its product type derived from the number's prefix and no Tripletex id remembered until the product has been synced to Tripletex

### Requirement: Create, update, and soft-delete a product
The system SHALL allow a user to create a product with a product type (`TJN` or `PRD`), a number, and a name: the system SHALL prefix the given number with the product type (unless the number already carries that prefix), persist the product locally first with an fms_ros-assigned id, and SHALL then attempt to push it to Tripletex as a new product and to Resco, remembering whichever ids are returned. A push failure to either system SHALL NOT fail the create; the create response SHALL include a warning identifying which system(s) the push failed for and stating that the sync needs to be retried. The system SHALL allow a user to update a product's type, number, or name, persisting the change locally first (with the number re-prefixed per the product type as needed) and then attempting to push the same change to the corresponding Tripletex product (if the product has a remembered Tripletex id) and Resco record (if it has a remembered Resco id); a push failure SHALL NOT fail the update, and the update response SHALL include the same kind of warning. The system SHALL allow a user to soft-delete a product. A soft-deleted product SHALL NOT be permanently removed, and SHALL NOT be deleted from Tripletex.

#### Scenario: Creating a product
- **WHEN** a user creates a product with a product type, a number, and a name
- **THEN** the system prefixes the number with the product type as needed, persists a local product with an fms_ros-assigned id, the resulting number, the product type, and the name the user provided, and attempts to push it to Tripletex and Resco

#### Scenario: Creating a product when Tripletex and/or Resco is unreachable
- **WHEN** a user creates a product while Tripletex and/or Resco cannot be reached or returns an error
- **THEN** the product is still persisted locally with an fms_ros-assigned id, and the create response includes a warning naming the system(s) the sync failed for

#### Scenario: Updating a product
- **WHEN** a user updates a product's type, number, or name
- **THEN** the system persists the change locally (with the number re-prefixed per the product type as needed) and attempts to push the same change to the corresponding Tripletex product and Resco record, for whichever of those the product has a remembered id for

#### Scenario: Updating a product when the push fails
- **WHEN** a user updates a product's fields and the push to Tripletex and/or Resco fails
- **THEN** the local update still succeeds, and the update response includes a warning naming the system(s) the sync failed for

#### Scenario: Soft-deleting a product
- **WHEN** a user soft-deletes a product
- **THEN** the system marks it deleted locally rather than removing it, and does not delete or otherwise modify the corresponding record in Tripletex

#### Scenario: A soft-deleted product stays excluded after a later Tripletex sync
- **WHEN** a product is soft-deleted in fms_ros, and a later Tripletex/Resco bootstrap sync runs
- **THEN** that product is excluded from the bootstrap sync's candidates, and its corresponding Tripletex/Resco record (if any) is left unmodified

## REMOVED Requirements

### Requirement: Sync products from Tripletex
**Reason**: fms_ros is now the system of record for products; Tripletex no longer originates new products this system needs to discover, so pulling Tripletex's product catalog into fms_ros (creating local records for ones fms_ros doesn't have, overwriting local fields with Tripletex's, soft-deleting/restoring based on Tripletex's list) no longer fits the ownership model.
**Migration**: See the new "Products are bootstrap-synced to Tripletex and Resco" requirement - it pushes fms_ros's own catalog outward instead of pulling Tripletex's in, and runs only on demand (never automatically).

## ADDED Requirements

### Requirement: Products are bootstrap-synced to Tripletex and Resco
The system SHALL let a user trigger, on demand only (never automatically at backend startup or otherwise), a bootstrap sync of every non-deleted product: for each such product with no remembered Tripletex id, the system SHALL create a corresponding product in Tripletex (using the same number-prefixing rule creation already uses) and remember the returned id; for each with no remembered Resco Product id, the system SHALL create a corresponding Product in Resco and remember the returned id; for each product that already has a remembered Tripletex id and/or Resco Product id, the system SHALL instead push that product's current local number and name as an update to the corresponding Tripletex product and/or Resco record. A failure syncing one product SHALL NOT prevent the sync from continuing to the remaining products.

#### Scenario: A product missing a Tripletex id is created in Tripletex
- **WHEN** a bootstrap sync runs and a local product has no remembered Tripletex id
- **THEN** the system creates a corresponding product in Tripletex using that product's current local number and name, and remembers the returned Tripletex id

#### Scenario: A product with a remembered Tripletex id is updated in Tripletex
- **WHEN** a bootstrap sync runs and a local product already has a remembered Tripletex id
- **THEN** the system pushes that product's current local number and name as an update to the corresponding Tripletex product, rather than creating a new one

#### Scenario: A product missing a Resco Product id is created in Resco
- **WHEN** a bootstrap sync runs and a local product has no remembered Resco Product id
- **THEN** the system creates a corresponding Product in Resco, and remembers the returned Resco Product id

#### Scenario: One product's sync failure does not block the rest
- **WHEN** a bootstrap sync processes multiple products and one push fails
- **THEN** the system continues syncing the remaining products and reports the failure for that one

#### Scenario: The bootstrap sync only runs on demand
- **WHEN** the backend starts
- **THEN** no product bootstrap sync runs automatically; it only runs when a user explicitly triggers it
