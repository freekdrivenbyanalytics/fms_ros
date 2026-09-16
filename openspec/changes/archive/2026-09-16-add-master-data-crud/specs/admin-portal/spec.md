## MODIFIED Requirements

### Requirement: Product list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted products and a detail view for each product showing its own fields, the employees who hold it, and the contract lines that require it. The system SHALL NOT provide any control on this view to change which employees or contract lines are associated with a product — those associations remain editable only from Employee Management (employees) or the Admin Portal's own Contracts view (contract lines).

#### Scenario: User browses the product list
- **WHEN** a user opens the product list view in the Admin Portal
- **THEN** the system shows every non-deleted product currently in the database

#### Scenario: User opens a product's detail view
- **WHEN** a user opens a product's detail view in the Admin Portal
- **THEN** the system shows that product's own fields, the employees who hold it, and the contract lines that require it, without any control to add or remove one

## ADDED Requirements

### Requirement: Create, update, and soft-delete a customer from the Admin Portal
The system SHALL let a user create a customer with a name, update a customer's fields, and soft-delete a customer, from the Admin Portal's Customers view.

#### Scenario: Creating a customer in the Admin Portal
- **WHEN** a user creates a customer from the Admin Portal
- **THEN** the system persists the new customer and it appears in the Customers list

#### Scenario: Updating a customer in the Admin Portal
- **WHEN** a user updates a customer's fields from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a customer in the Admin Portal
- **WHEN** a user soft-deletes a customer from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Customers list

### Requirement: Create, update, and soft-delete a customer location from the Admin Portal
The system SHALL let a user create a customer location for an existing customer with an address, update a customer location's address, and soft-delete a customer location, from the Admin Portal's Customer Locations view. This is in addition to, and does not replace, the existing coordinate-override control on this view.

#### Scenario: Creating a customer location in the Admin Portal
- **WHEN** a user creates a customer location for a customer from the Admin Portal
- **THEN** the system persists the new customer location and it appears in the Customer Locations list

#### Scenario: Updating a customer location's address in the Admin Portal
- **WHEN** a user updates a customer location's address from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a customer location in the Admin Portal
- **WHEN** a user soft-deletes a customer location from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Customer Locations list

### Requirement: Create, update, and soft-delete a product from the Admin Portal
The system SHALL let a user create a product with a product type, a number, and a name, update a product's type, number, or name, and soft-delete a product, from the Admin Portal's Products view.

#### Scenario: Creating a product in the Admin Portal
- **WHEN** a user creates a product from the Admin Portal
- **THEN** the system persists the new product and it appears in the Products list

#### Scenario: Updating a product in the Admin Portal
- **WHEN** a user updates a product's type, number, or name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a product in the Admin Portal
- **WHEN** a user soft-deletes a product from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Products list
