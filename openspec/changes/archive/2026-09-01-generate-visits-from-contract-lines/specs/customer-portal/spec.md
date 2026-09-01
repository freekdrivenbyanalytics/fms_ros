## ADDED Requirements

### Requirement: Contract line rows show their generated service visits
The system SHALL show, for each contract line displayed in the Customer Portal's Contracts view, the service visits generated from it, including each visit's requested date and status.

#### Scenario: Viewing a contract line's generated visits
- **WHEN** a user views a contract line in the Customer Portal's Contracts view
- **THEN** the system shows the service visits generated from that contract line, each with its requested date and status (unassigned or assigned)

#### Scenario: A contract line with no visits yet
- **WHEN** a user views a contract line that has no service visits
- **THEN** the system shows that it has no visits, rather than an error or a blank section
