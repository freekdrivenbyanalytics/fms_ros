## MODIFIED Requirements

### Requirement: Customer Portal is a separate top-level area
The system SHALL provide the Customer Portal as a top-level area reachable via a landing entry point distinct from the Planning application's own navigation, sharing no header or in-app navigation menu with Manual Assignment or Day Planning, except for a small, consistent set of cross-portal links (one per other portal) letting a user jump directly to the Planning application, Employee Management, or the Admin Portal.

#### Scenario: User reaches the Customer Portal
- **WHEN** a user navigates to the Customer Portal's entry point
- **THEN** the system shows the Customer Portal without any Planning-application navigation (Manual Assignment / Day Planning) visible alongside it, other than the cross-portal links

#### Scenario: Customer Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Customer Portal
- **THEN** any customer, customer location, or contract visible in the Planning application is also visible in the Customer Portal, and vice versa

#### Scenario: Customer Portal links to every other portal
- **WHEN** a user views the Customer Portal's sidebar
- **THEN** it shows a link to the Planning application, a link to Employee Management, and a link to the Admin Portal
