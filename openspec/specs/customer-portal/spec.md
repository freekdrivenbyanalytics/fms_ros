# customer-portal Specification

## Purpose

Gives a business user a simple, read-only way to browse the master data already held by the shared backend — employees, customers, customer locations, contracts, skills, and regions — and how those entities relate to each other, in a frontend area kept clearly separate from the Planning application.

## Requirements

### Requirement: Customer Portal is a separate top-level area
The system SHALL provide the Customer Portal as a top-level area reachable via a landing entry point distinct from the Planning application's own navigation, sharing no header or navigation elements with Manual Assignment or Day Planning.

#### Scenario: User reaches the Customer Portal
- **WHEN** a user navigates to the Customer Portal's entry point
- **THEN** the system shows the Customer Portal without any Planning-application navigation (Manual Assignment / Day Planning) visible alongside it

#### Scenario: Customer Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Customer Portal
- **THEN** any employee, customer, customer location, contract, skill, or region visible in the Planning application is also visible in the Customer Portal, and vice versa

### Requirement: List view for each master-data entity
The system SHALL provide, within the Customer Portal, a list view for each of: Employees, Customers, Customer Locations, Contracts, Skills, and Regions.

#### Scenario: User browses an entity list
- **WHEN** a user opens one of the six entity list views in the Customer Portal
- **THEN** the system shows every record of that entity type currently in the database

### Requirement: Detail view shows an item and its relationships
The system SHALL let a user open an item from any of the six list views to see a detail view containing that item's own fields and its relationships to other master-data entities.

#### Scenario: Customer detail
- **WHEN** a user opens a Customer's detail view
- **THEN** the system shows that customer's own fields and the list of Customer Locations belonging to that customer

#### Scenario: Customer Location detail
- **WHEN** a user opens a Customer Location's detail view
- **THEN** the system shows that location's own fields, the Customer it belongs to, the Region it is in, and the Contracts at that location

#### Scenario: Contract detail
- **WHEN** a user opens a Contract's detail view
- **THEN** the system shows that contract's own fields, the Customer Location it applies to, and the Skills it requires

#### Scenario: Employee detail
- **WHEN** a user opens an Employee's detail view
- **THEN** the system shows that employee's own fields, the Regions they are scoped to, and the Skills they possess

#### Scenario: Skill detail
- **WHEN** a user opens a Skill's detail view
- **THEN** the system shows that skill's own fields, the Employees who possess it, and the Contracts that require it

#### Scenario: Region detail
- **WHEN** a user opens a Region's detail view
- **THEN** the system shows that region's own fields, the Employees scoped to it, and the Customer Locations located in it

### Requirement: Customer Portal is read-only
The system SHALL NOT provide any create, edit, or delete action for master data anywhere in the Customer Portal.

#### Scenario: No mutation affordance
- **WHEN** a user views any list or detail view in the Customer Portal
- **THEN** the system provides no control to create, edit, or delete an employee, customer, customer location, contract, skill, or region
