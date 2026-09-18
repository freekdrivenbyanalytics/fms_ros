## MODIFIED Requirements

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
