## MODIFIED Requirements

### Requirement: Admin Portal is a separate top-level area
The system SHALL provide the Admin Portal as a top-level area reachable via a landing entry point distinct from the Planning application's navigation, the Customer Portal, and Employee Management, sharing no header or navigation elements with any of them.

#### Scenario: User reaches the Admin Portal
- **WHEN** a user navigates to the Admin Portal's entry point
- **THEN** the system shows the Admin Portal without any Planning-application, Customer Portal, or Employee Management navigation visible alongside it

#### Scenario: Admin Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Admin Portal
- **THEN** any region, product, contract, or customer location visible in the Planning application is also visible in the Admin Portal, and vice versa

### Requirement: Contract list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted contracts and a detail view for each contract showing its own fields, the customer it belongs to, and its contract lines, each showing its customer location, dates, interval, duration, and required products.

#### Scenario: User browses the contract list
- **WHEN** a user opens the contract list view in the Admin Portal
- **THEN** the system shows every non-deleted contract currently in the database

#### Scenario: User opens a contract's detail view
- **WHEN** a user opens a contract's detail view in the Admin Portal
- **THEN** the system shows that contract's own fields, the customer it belongs to, and its contract lines

### Requirement: Create, update, and soft-delete a contract line from the Admin Portal
The system SHALL let a user create a contract line under a contract — for one of that contract's customer's locations — update its customer location, dates, interval, duration, and required products, and soft-delete it, from the Admin Portal's Contract detail view.

#### Scenario: Creating a contract line in the Admin Portal
- **WHEN** a user creates a contract line under a contract from the Admin Portal, selecting one of that contract's customer's locations
- **THEN** the system persists the new contract line and it appears under that contract

#### Scenario: Updating a contract line in the Admin Portal
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required products from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract line in the Admin Portal
- **WHEN** a user soft-deletes a contract line from the Admin Portal
- **THEN** the system marks it deleted, it no longer appears under its contract, and any service visits already generated from it (and any assignment made against one of those visits) are permanently removed

## REMOVED Requirements

### Requirement: Skill list and detail views
**Reason**: Skills are replaced by the read-only Products view (see "Product list and detail views" below), sourced from Tripletex instead of locally managed.
**Migration**: Use the Admin Portal's new Products view.

### Requirement: Create, update, and soft-delete a skill from the Admin Portal
**Reason**: Products are read-only locally, sourced entirely from Tripletex; there is no local create/rename/delete for the replacement concept.
**Migration**: Use the Admin Portal's new "Refresh products from Tripletex" action.

### Requirement: Skill cross-references are read-only in the Admin Portal
**Reason**: Replaced by the equivalent read-only cross-reference behavior on the new Products view.
**Migration**: See "Product list and detail views" below.

## ADDED Requirements

### Requirement: Product list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted products and a detail view for each product showing its own fields, the employees who hold it, and the contract lines that require it. The system SHALL NOT provide any control to create, edit, or delete a product, or to change which employees or contract lines are associated with it — products are read-only locally, and those associations remain editable only from Employee Management (employees) or the Admin Portal's own Contracts view (contract lines).

#### Scenario: User browses the product list
- **WHEN** a user opens the product list view in the Admin Portal
- **THEN** the system shows every non-deleted product currently in the database

#### Scenario: User opens a product's detail view
- **WHEN** a user opens a product's detail view in the Admin Portal
- **THEN** the system shows that product's own fields, the employees who hold it, and the contract lines that require it, without any control to add or remove one

### Requirement: Refresh products from Tripletex
The system SHALL provide a control on the Admin Portal's Products view that triggers an on-demand Tripletex product sync, and SHALL refresh the Products view's data after the sync completes.

#### Scenario: Planner refreshes products
- **WHEN** a user activates the Refresh control on the Products view
- **THEN** the system triggers a Tripletex product sync, and once it completes, the Products view reflects the resulting data
