## MODIFIED Requirements

### Requirement: Admin Portal is a separate top-level area
The system SHALL provide the Admin Portal as a top-level area reachable via a landing entry point distinct from the Planning application's navigation, the Customer Portal, and Employee Management, sharing no header or navigation elements with any of them.

#### Scenario: User reaches the Admin Portal
- **WHEN** a user navigates to the Admin Portal's entry point
- **THEN** the system shows the Admin Portal without any Planning-application, Customer Portal, or Employee Management navigation visible alongside it

#### Scenario: Admin Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Admin Portal
- **THEN** any region or skill visible in the Planning application is also visible in the Admin Portal, and vice versa

## ADDED Requirements

### Requirement: Skill list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted skills and a detail view for each skill showing its own fields, the employees who hold it, and the contract lines that require it.

#### Scenario: User browses the skill list
- **WHEN** a user opens the skill list view in the Admin Portal
- **THEN** the system shows every non-deleted skill currently in the database

#### Scenario: User opens a skill's detail view
- **WHEN** a user opens a skill's detail view in the Admin Portal
- **THEN** the system shows that skill's own fields, the employees who hold it, and the contract lines that require it

### Requirement: Create, update, and soft-delete a skill from the Admin Portal
The system SHALL let a user create a skill with a name, update its name, and soft-delete it, from the Admin Portal.

#### Scenario: Creating a skill in the Admin Portal
- **WHEN** a user creates a skill from the Admin Portal
- **THEN** the system persists the new skill and it appears in the skill list

#### Scenario: Updating a skill's name in the Admin Portal
- **WHEN** a user updates a skill's name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a skill in the Admin Portal
- **WHEN** a user soft-deletes a skill from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the skill list

### Requirement: Skill cross-references are read-only in the Admin Portal
The system SHALL NOT provide any control in the Admin Portal to change which employees or contract lines are associated with a skill; those associations remain editable only from Employee Management (employees) or the Customer Portal's Contracts view (contract lines).

#### Scenario: No employee-assignment control on the skill detail view
- **WHEN** a user views a skill's detail view in the Admin Portal
- **THEN** the system shows the employees who hold that skill without any control to add or remove one

#### Scenario: No contract-line-assignment control on the skill detail view
- **WHEN** a user views a skill's detail view in the Admin Portal
- **THEN** the system shows the contract lines that require that skill without any control to add or remove one
