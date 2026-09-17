## MODIFIED Requirements

### Requirement: Employee Management is a separate top-level area
The system SHALL provide Employee Management as a top-level area reachable via a landing entry point distinct from both the Planning application's navigation and the Customer Portal, sharing no header or in-app navigation menu with either, except for a small, consistent set of cross-portal links (one per other portal) letting a user jump directly to the Planning application, the Customer Portal, or the Admin Portal.

#### Scenario: User reaches Employee Management
- **WHEN** a user navigates to the Employee Management entry point
- **THEN** the system shows Employee Management without any Planning-application or Customer Portal in-app navigation menu visible alongside it, other than the cross-portal links

#### Scenario: Employee Management and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves Employee Management
- **THEN** any employee visible in the Planning application is also visible in Employee Management, and vice versa

#### Scenario: Employee Management links to every other portal
- **WHEN** a user views Employee Management's sidebar
- **THEN** it shows a link to the Planning application, a link to the Customer Portal, and a link to the Admin Portal

## ADDED Requirements

### Requirement: Viewing-as employee selector in Employee Management
The system SHALL let a user pick one specific employee, or "All employees", from a selector in Employee Management's sidebar, filtering the employee list and its scoped content to that choice.

#### Scenario: Selecting a specific employee
- **WHEN** a user picks a specific employee from the sidebar selector
- **THEN** the employee list shows only that employee

#### Scenario: Selecting "All employees"
- **WHEN** a user picks "All employees" from the sidebar selector, or has not made a selection yet
- **THEN** the employee list shows every non-deleted employee, unfiltered

### Requirement: Select all skills on the employee form
The system SHALL let a user, from the employee create or edit form, select every existing skill in one action instead of checking each one individually.

#### Scenario: Selecting all skills at once
- **WHEN** a user activates the "select all skills" control on the employee form
- **THEN** every existing skill's checkbox becomes checked
