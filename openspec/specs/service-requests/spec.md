# service-requests Specification

## Purpose

Represents a customer's request for an extra, non-contracted product or service at one of their locations, submitted from the Customer Portal dashboard for staff to follow up on manually — not an automated ordering or billing system.

## Requirements

### Requirement: Service request data model
The system SHALL persist each service request with a unique identifier, the customer it was made by, the customer location it applies to, the requested product, an optional note, a status (`pending` or `acknowledged`, defaulting to `pending`), and when it was created.

#### Scenario: Service request is persisted with required fields
- **WHEN** a service request is created with a customer, a customer location belonging to that customer, and a product
- **THEN** the system persists the request with status `pending` and all fields are retrievable unchanged

### Requirement: Create a service request
The system SHALL let a customer (or an admin previewing as one) submit a service request specifying one of the customer's own locations and a non-deleted product of type `PRD`. The system SHALL reject a request naming a location that does not belong to the specified customer, or a product that is not a non-deleted `PRD`-type product.

#### Scenario: Creating a valid request
- **WHEN** a request is submitted with a customer, one of that customer's own locations, and a non-deleted `PRD` product
- **THEN** the system persists a new pending service request

#### Scenario: Rejecting a request for another customer's location
- **WHEN** a request is submitted naming a location that does not belong to the specified customer
- **THEN** the system rejects the request

#### Scenario: Rejecting a request for a non-PRD or deleted product
- **WHEN** a request is submitted naming a product that is not a non-deleted `PRD`-type product
- **THEN** the system rejects the request

### Requirement: List and acknowledge service requests
The system SHALL provide a staff-facing API to list all service requests (optionally filtered by status) and to mark a pending request as `acknowledged`.

#### Scenario: Listing pending requests
- **WHEN** staff request the list of service requests filtered to `pending`
- **THEN** the system returns every request with status `pending`, each with its customer, location, product, note, and creation time

#### Scenario: Acknowledging a request
- **WHEN** staff mark a pending service request as acknowledged
- **THEN** the system persists its status as `acknowledged` and it no longer appears in the default pending-requests list
