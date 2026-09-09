## Purpose

Represents the subset of Tripletex's product catalog — products whose number starts with "TJN" — used to qualify which employees can perform which contract lines' service visits, sourced entirely from Tripletex rather than locally managed.

## ADDED Requirements

### Requirement: Product data model
The system SHALL persist each product with a unique identifier (Tripletex's own product id), a product number, a product name, and a soft-delete flag.

#### Scenario: Product is persisted with required fields
- **WHEN** a product record is created with id, number, and name
- **THEN** the system persists the product and all fields are retrievable unchanged

### Requirement: Sync products from Tripletex
The system SHALL let a user trigger an on-demand sync of products from Tripletex, scoped to only products whose number starts with "TJN". Syncing SHALL create a local product for each matching Tripletex product not already present (keyed by Tripletex's own id), update the name of any that already exist, soft-delete any locally present product no longer returned by Tripletex, and restore (clear the soft-delete flag of) any previously soft-deleted product that reappears.

#### Scenario: Only TJN-numbered products are synced
- **WHEN** a product sync runs and Tripletex's product catalog includes products whose numbers do not start with "TJN"
- **THEN** the system does not create or update a local product for any of them

#### Scenario: A new TJN product is created
- **WHEN** a product sync runs and Tripletex has a TJN-numbered product with no corresponding local product
- **THEN** the system creates a local product for it, keyed by Tripletex's id

#### Scenario: A product no longer in Tripletex is soft-deleted
- **WHEN** a product sync runs and a locally present, non-deleted product's Tripletex id is no longer returned among matching products
- **THEN** the system marks that local product deleted

#### Scenario: A reappearing product is restored
- **WHEN** a product sync runs and a locally present, soft-deleted product's Tripletex id is returned again among matching products
- **THEN** the system clears that product's deleted flag

### Requirement: List products
The system SHALL provide an API to retrieve the list of all products, excluding products marked deleted by default.

#### Scenario: Retrieve all products
- **WHEN** a client requests the list of products
- **THEN** the system returns all non-deleted persisted products

#### Scenario: Deleted product is excluded from the list
- **WHEN** a caller requests the list of products
- **THEN** products marked deleted are not included in the result
