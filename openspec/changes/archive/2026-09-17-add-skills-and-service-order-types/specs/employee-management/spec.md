## MODIFIED Requirements

### Requirement: Employee list and detail views
The system SHALL provide, within Employee Management, a list view of all non-deleted employees and a detail view for each employee showing its own fields, the regions it is scoped to, the skills it holds, its schedule templates, and its day overrides.

#### Scenario: User browses the employee list
- **WHEN** a user opens the employee list view in Employee Management
- **THEN** the system shows every non-deleted employee currently in the database

#### Scenario: User opens an employee's detail view
- **WHEN** a user opens an employee's detail view in Employee Management
- **THEN** the system shows that employee's own fields, its regions, its skills, its schedule templates, and its day overrides

### Requirement: Create, update, and soft-delete an employee from Employee Management
The system SHALL let a user create an employee (name, home location, regions, skills), update any of those fields, and soft-delete the employee, from Employee Management.

#### Scenario: Creating an employee in Employee Management
- **WHEN** a user creates an employee from Employee Management
- **THEN** the system persists the new employee and it appears in the employee list

#### Scenario: Updating an employee in Employee Management
- **WHEN** a user updates an employee's fields from Employee Management
- **THEN** the system persists the change

#### Scenario: Soft-deleting an employee in Employee Management
- **WHEN** a user soft-deletes an employee from Employee Management
- **THEN** the system marks it deleted and it no longer appears in the employee list
