## ADDED Requirements

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
