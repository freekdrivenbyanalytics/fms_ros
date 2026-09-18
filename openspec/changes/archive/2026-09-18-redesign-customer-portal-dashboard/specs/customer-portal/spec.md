## MODIFIED Requirements

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

## ADDED Requirements

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
