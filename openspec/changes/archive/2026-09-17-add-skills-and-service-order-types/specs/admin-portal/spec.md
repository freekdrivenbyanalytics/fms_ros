## MODIFIED Requirements

### Requirement: Product list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted products and a detail view for each product showing its own fields, its required skills and service order type, and the contract lines that require it. The system SHALL NOT provide any control on this view to change which contract lines are associated with a product — that association remains editable only from the Admin Portal's own Contracts view.

#### Scenario: User browses the product list
- **WHEN** a user opens the product list view in the Admin Portal
- **THEN** the system shows every non-deleted product currently in the database

#### Scenario: User opens a product's detail view
- **WHEN** a user opens a product's detail view in the Admin Portal
- **THEN** the system shows that product's own fields, its required skills and service order type, and the contract lines that require it, without any control to add or remove a contract line association

## ADDED Requirements

### Requirement: Skills view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted skills and a detail view for each showing its own fields and the products that require it.

#### Scenario: User browses the skills list
- **WHEN** a user opens the skills list view in the Admin Portal
- **THEN** the system shows every non-deleted skill currently in the database

#### Scenario: User opens a skill's detail view
- **WHEN** a user opens a skill's detail view in the Admin Portal
- **THEN** the system shows that skill's own fields and the products that require it

### Requirement: Create, update, and soft-delete a skill from the Admin Portal
The system SHALL let a user create a skill with a name, update its name, and soft-delete it, from the Admin Portal's Skills view.

#### Scenario: Creating a skill in the Admin Portal
- **WHEN** a user creates a skill from the Admin Portal
- **THEN** the system persists the new skill and it appears in the Skills list

#### Scenario: Updating a skill in the Admin Portal
- **WHEN** a user updates a skill's name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a skill in the Admin Portal
- **WHEN** a user soft-deletes a skill from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Skills list

### Requirement: Service Order Types view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted service order types and a detail view for each showing its own fields and the products assigned it.

#### Scenario: User browses the service order types list
- **WHEN** a user opens the service order types list view in the Admin Portal
- **THEN** the system shows every non-deleted service order type currently in the database

#### Scenario: User opens a service order type's detail view
- **WHEN** a user opens a service order type's detail view in the Admin Portal
- **THEN** the system shows that service order type's own fields and the products assigned it

### Requirement: Create, update, and soft-delete a service order type from the Admin Portal
The system SHALL let a user create a service order type with a name, update its name, and soft-delete it, from the Admin Portal's Service Order Types view.

#### Scenario: Creating a service order type in the Admin Portal
- **WHEN** a user creates a service order type from the Admin Portal
- **THEN** the system persists the new service order type and it appears in the Service Order Types list

#### Scenario: Updating a service order type in the Admin Portal
- **WHEN** a user updates a service order type's name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a service order type in the Admin Portal
- **WHEN** a user soft-deletes a service order type from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Service Order Types list

### Requirement: Product detail view shows and edits required skills and service order type
The system SHALL let a user, from the Admin Portal's Products view, see and edit which skills a product requires and which service order type it has.

#### Scenario: Viewing a product's skills and service order type
- **WHEN** a user opens a product's detail view in the Admin Portal
- **THEN** the system shows the skills it requires and its service order type, if any

#### Scenario: Editing a product's skills and service order type
- **WHEN** a user updates which skills a product requires or which service order type it has, from the Admin Portal
- **THEN** the system persists the change
