## ADDED Requirements

### Requirement: Extend recurring visits from the Admin Portal
The system SHALL let a user, from the Admin Portal's Contracts view, trigger the extend-visits operation for every open-ended contract line at once. While the operation is in progress the system SHALL indicate that it is running, and SHALL show a result or error message once it completes.

#### Scenario: Triggering extend-visits
- **WHEN** a user clicks the "Extend recurring visits" action in the Admin Portal's Contracts view
- **THEN** the system triggers the extend-visits operation and, once it completes, shows a result message

#### Scenario: Extension in progress is indicated
- **WHEN** a user triggers extend-visits and it has not yet completed
- **THEN** the system shows that it is in progress and disables re-triggering it until it finishes

#### Scenario: A failed extension is reported
- **WHEN** the extend-visits operation fails
- **THEN** the system shows an error message rather than silently discarding the failure
