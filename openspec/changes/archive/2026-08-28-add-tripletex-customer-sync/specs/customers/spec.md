## MODIFIED Requirements

### Requirement: Customer data model
The system SHALL persist each customer using Tripletex as the source of truth: each customer's unique identifier SHALL be the id Tripletex assigns to it, and the customer's fields SHALL be set from the corresponding Tripletex customer record.

#### Scenario: Customer is persisted with required fields
- **WHEN** a customer record is created from a Tripletex customer
- **THEN** the system persists the customer using that Tripletex customer's id as its unique identifier, with its fields set from the corresponding Tripletex customer's fields, and both the identifier and fields are retrievable unchanged

## ADDED Requirements

### Requirement: Customers are synced from Tripletex
The system SHALL fetch the full list of customers from Tripletex and reconcile them into the locally persisted customers: a Tripletex customer not yet persisted locally SHALL be added, a Tripletex customer already persisted locally SHALL have its fields updated to match Tripletex, and a locally persisted customer no longer present in Tripletex SHALL be marked deleted (via a delete flag) rather than removed, leaving any customer locations, contracts, service visits, and assignments that depend on it unaffected. A locally persisted customer previously marked deleted that reappears in Tripletex SHALL have its deleted mark cleared and its fields overwritten to match Tripletex.

#### Scenario: New Tripletex customer is added locally
- **WHEN** a sync runs and Tripletex includes a customer not yet persisted locally
- **THEN** the system creates a local customer record for it

#### Scenario: Changed Tripletex customer is updated locally
- **WHEN** a sync runs and a Tripletex customer's fields differ from the locally persisted record
- **THEN** the system updates the local record's fields to match Tripletex

#### Scenario: Removed Tripletex customer is marked deleted locally
- **WHEN** a sync runs and a locally persisted customer is no longer present in Tripletex
- **THEN** the system marks that customer as deleted, and its customer locations, contracts, service visits, and assignments remain persisted and unaffected

#### Scenario: A previously deleted customer reappears in Tripletex
- **WHEN** a sync runs and a locally persisted customer that was marked deleted is present in Tripletex again
- **THEN** the system clears that customer's deleted mark and updates its fields to match Tripletex

### Requirement: Deleted customers are hidden by default
The system SHALL exclude customers marked deleted from the customer list returned to callers by default.

#### Scenario: Deleted customer is excluded from the customer list
- **WHEN** a caller requests the list of customers
- **THEN** customers marked deleted are not included in the result

### Requirement: Customer changes are logged
The system SHALL record a log entry each time a sync creates a customer, updates a customer's fields, marks a customer deleted, or restores a previously deleted customer, capturing the customer's id, the type of change, and when it occurred.

#### Scenario: Customer creation is logged
- **WHEN** a sync creates a new local customer
- **THEN** the system records a log entry for that customer with change type "created"

#### Scenario: Customer field update is logged
- **WHEN** a sync updates an existing local customer's fields
- **THEN** the system records a log entry for that customer with change type "updated"

#### Scenario: Customer deletion is logged
- **WHEN** a sync marks a local customer deleted
- **THEN** the system records a log entry for that customer with change type "deleted"

#### Scenario: Customer restoration is logged
- **WHEN** a sync clears a local customer's deleted mark
- **THEN** the system records a log entry for that customer with change type "restored"

### Requirement: Customer sync triggers
The system SHALL run the Tripletex customer sync automatically each time the backend starts, and SHALL also support triggering the sync on demand. The backend SHALL remain able to start even when Tripletex is unreachable at startup.

#### Scenario: Sync runs on backend startup
- **WHEN** the backend starts and Tripletex is reachable
- **THEN** the system runs a Tripletex customer sync before serving requests that depend on customer data being current

#### Scenario: Sync can be triggered on demand
- **WHEN** a sync is triggered on demand
- **THEN** the system runs the same reconciliation as the startup sync

#### Scenario: Tripletex unreachable at startup does not block the backend
- **WHEN** the backend starts and Tripletex is unreachable
- **THEN** the backend still starts and serves requests, using whatever customer data was already persisted locally

### Requirement: Tripletex credentials stay server-side
The system SHALL NOT expose Tripletex credentials or session tokens to the frontend; all communication with Tripletex SHALL happen through the backend.

#### Scenario: Frontend never receives Tripletex credentials
- **WHEN** the frontend triggers a customer sync or displays synced customer data
- **THEN** no Tripletex credential or session token is present in any response the frontend receives
