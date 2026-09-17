# products Specification

## Purpose

Represents the subset of Tripletex's product catalog scoped to a recognized product type prefix ("TJN" for tjeneste/service, "PRD" for produkt/product), used to qualify which employees can perform which contract lines' service visits. Products may originate in Tripletex or be created locally in fms_ros — either way, Tripletex is the system of record and fms_ros stays in sync with it.

## Requirements

### Requirement: Product data model
The system SHALL persist each product with a unique identifier (Tripletex's own product id), a product number, a product type (`TJN` for tjeneste/service or `PRD` for produkt/product — derived from the product number's prefix), a product name, a soft-delete flag, and a remembered Resco Product ID once the product has been synced to Resco.

#### Scenario: Product is persisted with required fields
- **WHEN** a product record is created with id, number, and name
- **THEN** the system persists the product and all fields are retrievable unchanged, with its product type derived from the number's prefix

### Requirement: Sync products from Tripletex
The system SHALL let a user trigger an on-demand sync of products from Tripletex, scoped to only products whose number starts with a recognized product type prefix (`TJN` or `PRD`). Syncing SHALL create a local product for each matching Tripletex product not already present (keyed by Tripletex's own id), update the name and number of any that already exist, always deriving that product's product type from its number's actual prefix, soft-delete any locally present product no longer returned by Tripletex, and restore (clear the soft-delete flag of) any previously soft-deleted product that reappears.

#### Scenario: Only TJN-numbered products are synced
- **WHEN** a product sync runs and Tripletex's product catalog includes products whose numbers do not start with `TJN` or `PRD`
- **THEN** the system does not create or update a local product for any of them

#### Scenario: A new TJN product is created
- **WHEN** a product sync runs and Tripletex has a TJN- or PRD-numbered product with no corresponding local product
- **THEN** the system creates a local product for it, keyed by Tripletex's id, with its product type derived from the number's prefix

#### Scenario: A product no longer in Tripletex is soft-deleted
- **WHEN** a product sync runs and a locally present, non-deleted product's Tripletex id is no longer returned among matching products
- **THEN** the system marks that local product deleted

#### Scenario: A reappearing product is restored
- **WHEN** a product sync runs and a locally present, soft-deleted product's Tripletex id is returned again among matching products
- **THEN** the system clears that product's deleted flag

### Requirement: Create, update, and soft-delete a product
The system SHALL allow a user to create a product with a product type (`TJN` or `PRD`), a number, and a name: the system SHALL prefix the given number with the product type (unless the number already carries that prefix) before pushing it to Tripletex as a new product's number, and SHALL adopt Tripletex's returned id as the new product's own id. Only product numbers starting with a recognized product type prefix (`TJN` or `PRD`) are ever pulled from Tripletex by the regular product sync, so every product created through this endpoint stays within that scope and is never mistaken for deleted by a later sync. The system SHALL allow a user to update a product's type, number, or name, pushing the same prefixing logic and the resulting number/name to the corresponding Tripletex product; and to soft-delete a product. A soft-deleted product SHALL NOT be permanently removed, and SHALL NOT be deleted from Tripletex.

#### Scenario: Creating a product
- **WHEN** a user creates a product with a product type, a number, and a name
- **THEN** the system prefixes the number with the product type as needed, creates the corresponding product in Tripletex with that number, persists a local product using the id Tripletex returns, and that product is retrievable with the resulting number, the product type, and the name the user provided

#### Scenario: Updating a product
- **WHEN** a user updates a product's type, number, or name
- **THEN** the system persists the change locally (with the number re-prefixed per the product type as needed) and pushes the same change to the corresponding Tripletex product

#### Scenario: Soft-deleting a product
- **WHEN** a user soft-deletes a product
- **THEN** the system marks it deleted locally rather than removing it, and does not delete or otherwise modify the corresponding record in Tripletex

#### Scenario: A soft-deleted product stays excluded after a later Tripletex sync
- **WHEN** a product is soft-deleted in fms_ros, and a later Tripletex product sync runs while that product is still present and unchanged in Tripletex
- **THEN** the product remains excluded from the product list — the sync SHALL NOT treat its continued presence in Tripletex as a reason to undo the local soft-delete

### Requirement: List products
The system SHALL provide an API to retrieve the list of all products, excluding products marked deleted by default.

#### Scenario: Retrieve all products
- **WHEN** a client requests the list of products
- **THEN** the system returns all non-deleted persisted products

#### Scenario: Deleted product is excluded from the list
- **WHEN** a caller requests the list of products
- **THEN** products marked deleted are not included in the result

### Requirement: A product can require multiple skills
The system SHALL allow a product to require zero or more skills, and update to allow a user to set which skills a product requires.

#### Scenario: Product with multiple required skills
- **WHEN** a product is associated with two or more skills
- **THEN** each association is retrievable and the product's required skills include all of them

#### Scenario: Updating a product's required skills
- **WHEN** a user updates which skills a product requires
- **THEN** the system persists the change

### Requirement: A product has an optional service order type
The system SHALL allow a product to have at most one service order type, and let a user set or clear it.

#### Scenario: Product with a service order type
- **WHEN** a product is assigned a service order type
- **THEN** the product's service order type is retrievable

#### Scenario: Product with no service order type
- **WHEN** a product has never been assigned a service order type
- **THEN** the product's service order type is retrievable as unset

#### Scenario: Updating a product's service order type
- **WHEN** a user sets or clears a product's service order type
- **THEN** the system persists the change
