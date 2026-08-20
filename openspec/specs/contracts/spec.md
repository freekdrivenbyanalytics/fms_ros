# contracts Specification

## Purpose

Represents a recurring service agreement tied to a customer location, defining the interval, duration, and skill requirements of the service visits it generates.

## Requirements

### Requirement: Contract data model
The system SHALL persist each contract with a unique identifier, the customer location it applies to, a start date, an interval in days, a visit duration in minutes, and the skills it requires.

#### Scenario: Contract is persisted with required fields
- **WHEN** a contract is created with id, customer_location_id, start_date, interval_days, duration_minutes, and one or more required skills
- **THEN** the system persists the contract and all fields are retrievable unchanged

### Requirement: A contract can require multiple skills
The system SHALL allow a contract to require more than one skill.

#### Scenario: Contract with multiple required skills
- **WHEN** a contract is associated with two or more skills
- **THEN** each association is retrievable and the contract's required skills include all of them
