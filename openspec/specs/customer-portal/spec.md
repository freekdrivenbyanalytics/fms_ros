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
- **THEN** any customer, customer location, or contract visible in the Planning application is also visible in the Customer Portal, and vice versa

### Requirement: List view for each master-data entity
The system SHALL provide, within the Customer Portal, a list view for each of: Customers, Customer Locations, and Contracts.

#### Scenario: User browses an entity list
- **WHEN** a user opens one of the three entity list views in the Customer Portal
- **THEN** the system shows every record of that entity type currently in the database

### Requirement: Customer switcher scopes the Customers view
The system SHALL provide a customer switcher, present on every page of the Customer Portal, that lets a user select "All customers" (the default) or one specific customer. Selecting a specific customer SHALL cause the Customers view to show that customer's own detail page instead of the list of all customers; the other two entity views (Customer Locations, Contracts) SHALL remain unaffected by the switcher's selection. The system SHALL NOT perform any authentication or authorization based on the switcher's selection.

#### Scenario: Switcher defaults to All customers
- **WHEN** a user opens the Customer Portal without having made a selection
- **THEN** the switcher is set to "All customers" and the Customers view shows the full list of customers

#### Scenario: Selecting a specific customer scopes the Customers view
- **WHEN** a user selects a specific customer in the switcher
- **THEN** the Customers view shows only that customer's own detail page, not the list of all customers

#### Scenario: Other views remain unaffected
- **WHEN** a specific customer is selected in the switcher
- **THEN** the Customer Locations and Contracts views continue to show every record, unfiltered

#### Scenario: Switcher selection persists across pages
- **WHEN** a user navigates between the Customer Portal's entity views while a specific customer is selected
- **THEN** the switcher keeps showing that same customer as selected

#### Scenario: Returning to All customers restores the list
- **WHEN** a user selects "All customers" again after having selected a specific customer
- **THEN** the Customers view shows the full list of customers again

#### Scenario: Switcher does not restrict access
- **WHEN** a specific customer is selected in the switcher
- **THEN** the system does not prevent selecting any other customer, and does not restrict what data any other view shows — the selection is a display convenience only, not an access control

### Requirement: Customer id is visible
The system SHALL display each customer's unique identifier on the Customers list view and on that customer's detail view.

#### Scenario: Customers list shows id
- **WHEN** a user opens the Customers list view
- **THEN** each row shows that customer's id alongside its name

#### Scenario: Customer detail shows id
- **WHEN** a user opens a Customer's detail view
- **THEN** the view shows that customer's id

### Requirement: Detail view shows a Customer Portal record's own fields and relationships
The system SHALL let a user open an item from any of the three list views to see a detail view containing that item's own fields and its relationships to other master-data entities.

#### Scenario: Customer detail
- **WHEN** a user opens a Customer's detail view
- **THEN** the system shows that customer's own fields and the list of Customer Locations belonging to that customer, each shown as a link that opens that location's own detail view

#### Scenario: Customer Location detail
- **WHEN** a user opens a Customer Location's detail view
- **THEN** the system shows that location's own fields, the Customer it belongs to, the Region it is in, and the Contract Lines at that location

#### Scenario: Contract detail
- **WHEN** a user opens a Contract's detail view
- **THEN** the system shows that contract's own fields, the Customer it belongs to, and its Contract Lines, each showing its Customer Location, dates, interval, duration, and required Skills

### Requirement: Refresh customers from Tripletex
The system SHALL provide a control on the Customer Portal's Customers view that triggers an on-demand Tripletex customer sync, and SHALL refresh the Customers, Customer Locations, and Contracts views' data after the sync completes.

#### Scenario: Planner refreshes customers
- **WHEN** a user activates the Refresh control on the Customers view
- **THEN** the system triggers a Tripletex customer sync, and once it completes, the Customers, Customer Locations, and Contracts views reflect the resulting data

### Requirement: Customer Portal is fully read-only
The system SHALL NOT provide any create, edit, or delete action for any entity anywhere in the Customer Portal.

#### Scenario: No mutation affordance
- **WHEN** a user views any list or detail view in the Customer Portal
- **THEN** the system provides no control to create, edit, or delete that entity

### Requirement: Contract line rows show their generated service visits
The system SHALL show, for each contract line displayed in the Customer Portal's Contracts view, the service visits generated from it, including each visit's requested date and status.

#### Scenario: Viewing a contract line's generated visits
- **WHEN** a user views a contract line in the Customer Portal's Contracts view
- **THEN** the system shows the service visits generated from that contract line, each with its requested date and status (unassigned or assigned)

#### Scenario: A contract line with no visits yet
- **WHEN** a user views a contract line that has no service visits
- **THEN** the system shows that it has no visits, rather than an error or a blank section
