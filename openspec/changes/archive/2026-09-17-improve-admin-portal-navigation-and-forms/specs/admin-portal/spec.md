## MODIFIED Requirements

### Requirement: Admin Portal is a separate top-level area
The system SHALL provide the Admin Portal as a top-level area reachable via a landing entry point distinct from the Planning application's navigation, the Customer Portal, and Employee Management, sharing no header or in-app navigation menu with any of them, except for a small, consistent set of cross-portal links (one per other portal) letting a user jump directly to the Planning application, the Customer Portal, or Employee Management.

#### Scenario: User reaches the Admin Portal
- **WHEN** a user navigates to the Admin Portal's entry point
- **THEN** the system shows the Admin Portal without any Planning-application, Customer Portal, or Employee Management in-app navigation menu visible alongside it, other than the cross-portal links

#### Scenario: Admin Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Admin Portal
- **THEN** any region, product, contract, or customer location visible in the Planning application is also visible in the Admin Portal, and vice versa

#### Scenario: Admin Portal links to every other portal
- **WHEN** a user views the Admin Portal's sidebar
- **THEN** it shows a link to the Planning application, a link to the Customer Portal, and a link to Employee Management

## ADDED Requirements

### Requirement: Contract line form groups its schedule fields under a heading
The system SHALL show a "Schedule" heading above the contract-line form's start date, end date, interval, and duration fields in the Admin Portal, matching the existing "Required products" heading already shown above that field.

#### Scenario: Schedule fields are grouped under a heading
- **WHEN** a user opens the contract-line create or edit form in the Admin Portal
- **THEN** the start date, end date, interval, and duration fields appear together under a "Schedule" heading, the same way the required-products field appears under its own heading
