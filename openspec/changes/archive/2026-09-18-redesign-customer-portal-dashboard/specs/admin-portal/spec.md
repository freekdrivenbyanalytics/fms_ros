## ADDED Requirements

### Requirement: Service Requests view
The system SHALL provide, within the Admin Portal, a list view of pending service requests (customer, location, product, note, creation time), and a control to acknowledge one.

#### Scenario: Staff browses pending service requests
- **WHEN** a user opens the Service Requests view in the Admin Portal
- **THEN** the system shows every pending service request

#### Scenario: Acknowledging a request from the Admin Portal
- **WHEN** a user acknowledges a pending service request from the Admin Portal
- **THEN** the system marks it acknowledged and it no longer appears in the pending list
