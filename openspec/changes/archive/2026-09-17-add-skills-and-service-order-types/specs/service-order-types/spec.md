## Purpose

Represents a service order type — a classification of what kind of work a product represents (for example, general caretaking versus winter maintenance) — used to group and categorize products.

## ADDED Requirements

### Requirement: Service order type data model
The system SHALL persist each service order type with a unique identifier, a name, and a soft-delete flag.

#### Scenario: Service order type is persisted with required fields
- **WHEN** a service order type is created with a name
- **THEN** the system persists the service order type and its fields are retrievable unchanged

### Requirement: List service order types
The system SHALL provide an API to retrieve the list of all service order types, excluding those marked deleted by default.

#### Scenario: Retrieve all service order types
- **WHEN** a client requests the list of service order types
- **THEN** the system returns all non-deleted persisted service order types

#### Scenario: Deleted service order type is excluded from the list
- **WHEN** a caller requests the list of service order types
- **THEN** service order types marked deleted are not included in the result

### Requirement: Create, update, and soft-delete a service order type
The system SHALL allow a user to create a service order type with a name, update its name, and soft-delete it. A soft-deleted service order type SHALL NOT be permanently removed.

#### Scenario: Creating a service order type
- **WHEN** a user creates a service order type with a name
- **THEN** the system persists a new service order type with that name

#### Scenario: Updating a service order type
- **WHEN** a user updates a service order type's name
- **THEN** the system persists the change, and every product already assigned that service order type reflects the new name

#### Scenario: Soft-deleting a service order type
- **WHEN** a user soft-deletes a service order type
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default service order type list
