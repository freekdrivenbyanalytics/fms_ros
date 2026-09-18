# customer-portal Specification

## Purpose

Gives a business user a simple, read-only way to browse the master data already held by the shared backend — employees, customers, customer locations, contracts, products, and regions — and how those entities relate to each other, in a frontend area kept clearly separate from the Planning application.

## Requirements

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

### Requirement: List view for each master-data entity
The system SHALL provide, within the Customer Portal, a list view for each of: Customers, Customer Locations, and Contracts.

#### Scenario: User browses an entity list
- **WHEN** a user opens one of the three entity list views in the Customer Portal
- **THEN** the system shows every record of that entity type currently in the database

### Requirement: Customer switcher scopes the Customers view
The system SHALL provide a customer switcher, present on every page of the Customer Portal, that lets an admin session select "All customers" (the default) or one specific customer from every customer in the system; a customer session SHALL NOT see this switcher at all and is instead always scoped to exactly the customer(s) assigned to it (see the user-auth capability). For an admin session, selecting a specific customer SHALL cause the Customers view to show that customer's own detail page instead of the list of all customers; the other two entity views (Customer Locations, Contracts) SHALL remain unaffected by the switcher's selection. For an admin session, the switcher SHALL remain a display convenience only: it does not grant or restrict access, since an admin session already has access to every customer regardless of the switcher's selection. Actual access control — which customers a session can see at all — SHALL be governed entirely by the user-auth capability's login and customer-assignment rules, not by the switcher.

#### Scenario: Switcher defaults to All customers
- **WHEN** an admin opens the Customer Portal without having made a selection
- **THEN** the switcher is set to "All customers" and the Customers view shows the full list of customers

#### Scenario: Selecting a specific customer scopes the Customers view
- **WHEN** an admin selects a specific customer in the switcher
- **THEN** the Customers view shows only that customer's own detail page, not the list of all customers

#### Scenario: Other views remain unaffected
- **WHEN** a specific customer is selected in the switcher
- **THEN** the Customer Locations and Contracts views continue to show every record, unfiltered

#### Scenario: Switcher selection persists across pages
- **WHEN** an admin navigates between the Customer Portal's entity views while a specific customer is selected
- **THEN** the switcher keeps showing that same customer as selected

#### Scenario: Returning to All customers restores the list
- **WHEN** an admin selects "All customers" again after having selected a specific customer
- **THEN** the Customers view shows the full list of customers again

#### Scenario: Switcher does not restrict access
- **WHEN** a specific customer is selected in the switcher during an admin session
- **THEN** the system does not prevent selecting any other customer, and does not restrict what data any other view shows — the selection is a display convenience only, not an access control

#### Scenario: A customer session sees no switcher
- **WHEN** a customer user opens the Customer Portal
- **THEN** the system shows no "All customers"/specific-customer switcher, and every view is already scoped to that user's assigned customer(s)

#### Scenario: A customer session's data is restricted by assignment, not by any switcher
- **WHEN** a customer user views the Customer Portal
- **THEN** what they see is limited to their assigned customer(s) by their login session, independent of any display-only switcher

### Requirement: Customer id is visible
The system SHALL display each customer's unique identifier on the Customers list view and on that customer's detail view.

#### Scenario: Customers list shows id
- **WHEN** a user opens the Customers list view
- **THEN** each row shows that customer's id alongside its name

#### Scenario: Customer detail shows id
- **WHEN** a user opens a Customer's detail view
- **THEN** the view shows that customer's id

### Requirement: Detail view shows a Customer Portal record's own fields and relationships
The system SHALL let a user open a Customer Location or Contract from its list view to see a detail view containing that item's own fields and its relationships to other master-data entities. Opening a specific Customer, whether from the Customers list or via the customer switcher, SHALL instead show that customer's consolidated dashboard (see "Customer dashboard for a selected customer") rather than a separate Customer detail page.

#### Scenario: Customer detail
- **WHEN** a user opens a specific customer, whether from the Customers list or via the customer switcher
- **THEN** the system shows that customer's consolidated dashboard (locations, contracts, planned visits, offers placeholder, and the extra-services request flow) rather than a standalone Customer detail page

#### Scenario: Customer Location detail
- **WHEN** a user opens a Customer Location's detail view
- **THEN** the system shows that location's own fields, the Customer it belongs to, the Region it is in, and the Contract Lines at that location

#### Scenario: Contract detail
- **WHEN** a user opens a Contract's detail view
- **THEN** the system shows that contract's own fields, the Customer it belongs to, and its Contract Lines, each showing its Customer Location, dates, interval, duration, and required Products

### Requirement: Refresh customers from Tripletex
The system SHALL provide a control on the Customer Portal's Customers view that triggers an on-demand Tripletex customer sync, and SHALL refresh the Customers, Customer Locations, and Contracts views' data after the sync completes.

#### Scenario: Planner refreshes customers
- **WHEN** a user activates the Refresh control on the Customers view
- **THEN** the system triggers a Tripletex customer sync, and once it completes, the Customers, Customer Locations, and Contracts views reflect the resulting data

### Requirement: Customer Portal is fully read-only
The system SHALL NOT provide any create, edit, or delete action for any entity anywhere in the Customer Portal, except booking an ad-hoc visit into a free slot from the Contracts view.

#### Scenario: No mutation affordance
- **WHEN** a user views any list or detail view in the Customer Portal other than a contract line's "Book ad-hoc visit" action
- **THEN** the system provides no control to create, edit, or delete that entity

#### Scenario: Ad-hoc booking is the one exception
- **WHEN** a user books a free slot for a contract line in the Customer Portal's Contracts view
- **THEN** the system creates the resulting service visit and its assignment, as this is the one action the Customer Portal permits

### Requirement: Contract line rows show their generated service visits
The system SHALL show, for each contract line displayed in the Customer Portal's Contracts view, the service visits generated from it, including each visit's requested date and status.

#### Scenario: Viewing a contract line's generated visits
- **WHEN** a user views a contract line in the Customer Portal's Contracts view
- **THEN** the system shows the service visits generated from that contract line, each with its requested date and status (unassigned or assigned)

#### Scenario: A contract line with no visits yet
- **WHEN** a user views a contract line that has no service visits
- **THEN** the system shows that it has no visits, rather than an error or a blank section

### Requirement: Book an ad-hoc visit from the Customer Portal
The system SHALL let a user, from a contract line displayed in the Customer Portal's Contracts view, view its available free slots and book one. This action SHALL be available regardless of the customer switcher's selection, consistent with the Contracts view otherwise being unaffected by it.

#### Scenario: Viewing free slots for a contract line
- **WHEN** a user opens the "Book ad-hoc visit" action for a contract line in the Customer Portal
- **THEN** the system shows that contract line's available free slots

#### Scenario: A contract line with no free slots shows that clearly
- **WHEN** a user opens the "Book ad-hoc visit" action for a contract line with no available free slots
- **THEN** the system shows that no slots are available, rather than an error or a blank list

#### Scenario: Booking a slot
- **WHEN** a user selects one of a contract line's shown free slots and confirms
- **THEN** the system books that slot and shows the resulting visit's date, time, and assigned employee

### Requirement: Customer dashboard for a selected customer
The system SHALL show, on one page, for whichever customer is currently in scope (selected via the switcher, or the sole customer of a logged-in customer session): that customer's own fields, all of their customer locations, all of their contracts (each with its contract lines), and their upcoming planned service visits (visits with a requested date today or later, across all of their contract lines), ordered by date.

#### Scenario: Dashboard shows locations, contracts, and visits together
- **WHEN** a customer becomes the one in scope in the Customer Portal
- **THEN** the system shows their locations, their contracts and contract lines, and their upcoming planned service visits, all on one page

#### Scenario: A customer with no upcoming visits shows that clearly
- **WHEN** a customer in scope has no service visits with a requested date today or later
- **THEN** the dashboard shows that there are no upcoming visits, rather than an empty section with no explanation

### Requirement: Offers placeholder on the dashboard
The system SHALL show an "Offers" section on the customer dashboard, styled as a task-like reminder block, that is empty in this change. No offer data or generation logic is part of this requirement.

#### Scenario: Offers section is present but empty
- **WHEN** a user views the customer dashboard
- **THEN** an "Offers" section is visible, showing that there are currently no offers, without implying any action is needed

### Requirement: Request an extra service from the dashboard
The system SHALL let a user, from the customer dashboard, browse the catalog of orderable extra products (non-deleted products of type `PRD`) and submit a request for one at a specific one of that customer's locations, optionally with a note. Submitting a request SHALL NOT create a contract, a contract line, or any Tripletex record — it SHALL only create a locally visible request for staff follow-up.

#### Scenario: Submitting an extra-service request
- **WHEN** a user selects an extra (`PRD`-type) product, one of the customer's locations, and submits
- **THEN** the system creates a pending service request for that customer, location, and product, and confirms the submission without creating any contract, contract line, or Tripletex record

#### Scenario: No PRD products available
- **WHEN** there are no non-deleted `PRD`-type products
- **THEN** the dashboard shows that no extra services are currently available, rather than an empty, unexplained picker
