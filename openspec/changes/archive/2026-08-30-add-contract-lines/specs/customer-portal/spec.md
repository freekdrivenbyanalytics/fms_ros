## ADDED Requirements

### Requirement: Create, update, and soft-delete a contract from the Customer Portal
The system SHALL let a user create a contract for a customer, update which customer it belongs to, and soft-delete it, from the Customer Portal's Contracts view.

#### Scenario: Creating a contract in the portal
- **WHEN** a user creates a contract for a customer from the Customer Portal
- **THEN** the system persists the new contract and it appears in the Contracts list

#### Scenario: Updating a contract in the portal
- **WHEN** a user updates a contract's customer from the Customer Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract in the portal
- **WHEN** a user soft-deletes a contract from the Customer Portal
- **THEN** the system marks it deleted, it no longer appears in the Contracts list, and its contract lines are also marked deleted

### Requirement: Create, update, and soft-delete a contract line from the Customer Portal
The system SHALL let a user create a contract line under a contract — for one of that contract's customer's locations — update its customer location, dates, interval, duration, and required skills, and soft-delete it, from the Customer Portal's Contract detail view.

#### Scenario: Creating a contract line in the portal
- **WHEN** a user creates a contract line under a contract from the Customer Portal, selecting one of that contract's customer's locations
- **THEN** the system persists the new contract line and it appears under that contract

#### Scenario: Updating a contract line in the portal
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required skills from the Customer Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract line in the portal
- **WHEN** a user soft-deletes a contract line from the Customer Portal
- **THEN** the system marks it deleted and it no longer appears under its contract, while any service visits already generated from it remain visible elsewhere in the app

## MODIFIED Requirements

### Requirement: Customer Portal is read-only
The system SHALL NOT provide any create, edit, or delete action for Employees, Customers, Customer Locations, Skills, or Regions anywhere in the Customer Portal. Contracts and Contract Lines are the exception: the Customer Portal SHALL let a user create, update, and soft-delete both.

#### Scenario: No mutation affordance
- **WHEN** a user views any Employees, Customers, Customer Locations, Skills, or Regions list or detail view in the Customer Portal
- **THEN** the system provides no control to create, edit, or delete that entity

#### Scenario: Contracts and Contract Lines are the exception
- **WHEN** a user views the Contracts area of the Customer Portal
- **THEN** the system provides controls to create, update, and soft-delete both contracts and contract lines

### Requirement: Detail view shows an item and its relationships
The system SHALL let a user open an item from any of the six list views to see a detail view containing that item's own fields and its relationships to other master-data entities.

#### Scenario: Customer detail
- **WHEN** a user opens a Customer's detail view
- **THEN** the system shows that customer's own fields and the list of Customer Locations belonging to that customer, each shown as a link that opens that location's own detail view

#### Scenario: Customer Location detail
- **WHEN** a user opens a Customer Location's detail view
- **THEN** the system shows that location's own fields, the Customer it belongs to, the Region it is in, and the Contract Lines at that location

#### Scenario: Contract detail
- **WHEN** a user opens a Contract's detail view
- **THEN** the system shows that contract's own fields, the Customer it belongs to, and its Contract Lines, each showing its Customer Location, dates, interval, duration, and required Skills

#### Scenario: Employee detail
- **WHEN** a user opens an Employee's detail view
- **THEN** the system shows that employee's own fields, the Regions they are scoped to, and the Skills they possess

#### Scenario: Skill detail
- **WHEN** a user opens a Skill's detail view
- **THEN** the system shows that skill's own fields, the Employees who possess it, and the Contract Lines that require it

#### Scenario: Region detail
- **WHEN** a user opens a Region's detail view
- **THEN** the system shows that region's own fields, the Employees scoped to it, and the Customer Locations located in it
