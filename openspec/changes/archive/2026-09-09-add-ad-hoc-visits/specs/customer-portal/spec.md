## MODIFIED Requirements

### Requirement: Customer Portal is fully read-only
The system SHALL NOT provide any create, edit, or delete action for any entity anywhere in the Customer Portal, except booking an ad-hoc visit into a free slot from the Contracts view.

#### Scenario: No mutation affordance
- **WHEN** a user views any list or detail view in the Customer Portal other than a contract line's "Book ad-hoc visit" action
- **THEN** the system provides no control to create, edit, or delete that entity

#### Scenario: Ad-hoc booking is the one exception
- **WHEN** a user books a free slot for a contract line in the Customer Portal's Contracts view
- **THEN** the system creates the resulting service visit and its assignment, as this is the one action the Customer Portal permits

## ADDED Requirements

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
