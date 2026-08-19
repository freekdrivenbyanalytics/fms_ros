# service-visits Specification

## Purpose

Represents customer service visits requested for scheduling, tracked through an unassigned/assigned lifecycle so planners can see what still needs an employee.

## Requirements

### Requirement: Service visit data model
The system SHALL persist each service visit with a unique identifier, customer name, address, geographic location (latitude, longitude), duration in minutes, requested date, and a status.

#### Scenario: Service visit is persisted with required fields
- **WHEN** a service visit is created with id, customer_name, address, latitude, longitude, duration_minutes, and requested_date
- **THEN** the system persists the service visit and all fields are retrievable unchanged

### Requirement: New service visits start unassigned
A newly created service visit SHALL have status `unassigned` until an assignment is created for it.

#### Scenario: New visit has unassigned status
- **WHEN** a service visit is created and no assignment exists for it
- **THEN** its status is `unassigned`

### Requirement: List service visits by assignment status
The system SHALL provide an API to retrieve service visits with their status, so unassigned visits and assigned visits can be distinguished.

#### Scenario: Retrieve visits with status
- **WHEN** a client requests the list of service visits
- **THEN** the system returns every visit together with its status of either `unassigned` or `assigned`
