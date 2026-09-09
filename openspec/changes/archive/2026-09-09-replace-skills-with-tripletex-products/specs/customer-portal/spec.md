## MODIFIED Requirements

### Requirement: Detail view shows a Customer Portal record's own fields and relationships
The system SHALL let a user open an item from any of the three list views to see a detail view containing that item's own fields and its relationships to other master-data entities.

#### Scenario: Customer detail
- **WHEN** a user opens a Customer's detail view
- **THEN** the system shows that customer's own fields and the list of Customer Locations belonging to that customer, each shown as a link that opens that location's own detail view

#### Scenario: Customer Location detail
- **WHEN** a user opens a Customer Location's detail view
- **THEN** the system shows that location's own fields, the Customer it belongs to, the Region it is in, and the Contract Lines at that location

#### Scenario: Contract detail
- **WHEN** a user opens a Contract's detail view
- **THEN** the system shows that contract's own fields, the Customer it belongs to, and its Contract Lines, each showing its Customer Location, dates, interval, duration, and required Products
