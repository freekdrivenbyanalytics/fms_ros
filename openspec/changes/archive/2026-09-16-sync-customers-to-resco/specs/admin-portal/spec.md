## ADDED Requirements

### Requirement: Customers view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted customers and a detail view for each showing its Tripletex-sourced fields (name, email, phone, organization number) and its Resco sync status.

#### Scenario: User browses the customer list
- **WHEN** a user opens the customer list view in the Admin Portal
- **THEN** the system shows every non-deleted customer currently in the database

#### Scenario: User opens a customer's detail view
- **WHEN** a user opens a customer's detail view in the Admin Portal
- **THEN** the system shows that customer's Tripletex-sourced fields and whether it has been synced to Resco

### Requirement: Sync customers and customer locations to Resco from the Admin Portal
The system SHALL provide a control on the Admin Portal's Customers view that triggers an on-demand Resco customer sync, and a control on the Customer Locations view that triggers an on-demand Resco customer location sync, each showing the returned summary (created/updated/skipped/failed counts).

#### Scenario: Planner syncs customers to Resco
- **WHEN** a user activates the "Sync to Resco" control on the Customers view
- **THEN** the system triggers a Resco customer sync and shows the resulting summary

#### Scenario: Planner syncs customer locations to Resco
- **WHEN** a user activates the "Sync to Resco" control on the Customer Locations view
- **THEN** the system triggers a Resco customer location sync and shows the resulting summary
