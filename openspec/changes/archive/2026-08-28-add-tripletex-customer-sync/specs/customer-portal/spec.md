## ADDED Requirements

### Requirement: Refresh customers from Tripletex
The system SHALL provide a control on the Customer Portal's Customers view that triggers an on-demand Tripletex customer sync, and SHALL refresh the Customers, Customer Locations, and Contracts views' data after the sync completes.

#### Scenario: Planner refreshes customers
- **WHEN** a user activates the Refresh control on the Customers view
- **THEN** the system triggers a Tripletex customer sync, and once it completes, the Customers, Customer Locations, and Contracts views reflect the resulting data
