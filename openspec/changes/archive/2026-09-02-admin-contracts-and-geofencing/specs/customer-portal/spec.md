## REMOVED Requirements

### Requirement: Customer Portal is read-only
**Reason**: Contracts and Contract Lines were the only exception to the Customer Portal's read-only rule, and their editing moves to the Admin Portal. The Customer Portal has no exceptions left.
**Migration**: Replaced by "Customer Portal is fully read-only" below.

### Requirement: Create, update, and soft-delete a contract from the Customer Portal
**Reason**: Contract management moves to the Admin Portal, alongside Regions and Skills. The Customer Portal keeps a read-only Contracts view.
**Migration**: Use the Admin Portal's Contracts view to create, update, or soft-delete a contract.

### Requirement: Create, update, and soft-delete a contract line from the Customer Portal
**Reason**: Contract line management moves to the Admin Portal along with its parent Contract.
**Migration**: Use the Admin Portal's Contract detail view to create, update, or soft-delete a contract line.

## ADDED Requirements

### Requirement: Customer Portal is fully read-only
The system SHALL NOT provide any create, edit, or delete action for any entity anywhere in the Customer Portal.

#### Scenario: No mutation affordance
- **WHEN** a user views any list or detail view in the Customer Portal
- **THEN** the system provides no control to create, edit, or delete that entity
