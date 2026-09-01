## MODIFIED Requirements

### Requirement: List service visits by assignment status
The system SHALL provide an API to retrieve service visits with their status, their contract line's customer location (customer name, address, region), duration, and required skills, so unassigned visits and assigned visits can be distinguished, located, and matched to a qualified employee. The API SHALL accept optional start-date and end-date filters that restrict the returned visits to those whose requested_date falls within the given range (inclusive); omitting either bound leaves that side of the range open.

#### Scenario: Retrieve visits with status
- **WHEN** a client requests the list of service visits
- **THEN** the system returns every visit together with its status of either `unassigned` or `assigned`, and the customer name, address, region, duration, and required skills of the contract line it was generated from

#### Scenario: Retrieve visits within a date range
- **WHEN** a client requests the list of service visits with a start-date and/or end-date filter
- **THEN** the system returns only visits whose requested_date falls within the given range, applying only the bounds that were provided

#### Scenario: No date filter returns every visit
- **WHEN** a client requests the list of service visits with no start-date or end-date filter
- **THEN** the system returns every visit regardless of requested_date, unchanged from today's behavior

## ADDED Requirements

### Requirement: Creating a contract line generates its service visits
The system SHALL, when a contract line is created, generate one unassigned service visit for the contract line's start_date and for every subsequent occurrence spaced interval_days apart, up to and including the contract line's end_date if it has one, or up to 365 days (one year) after start_date if it has no end_date. Each generated visit SHALL be linked to that contract line.

#### Scenario: Generating visits for a bounded contract line
- **WHEN** a contract line is created with a start_date, interval_days, and an end_date
- **THEN** the system creates one unassigned service visit for start_date and for every occurrence interval_days apart thereafter, up to and including end_date

#### Scenario: Generating visits for an open-ended contract line
- **WHEN** a contract line is created with a start_date and interval_days but no end_date
- **THEN** the system creates one unassigned service visit for start_date and for every occurrence interval_days apart thereafter, up to 365 days (one year) after start_date

#### Scenario: Generated visits are linked to their contract line
- **WHEN** a contract line's service visits are generated
- **THEN** each generated visit's contract_line_id refers to that contract line, and the visits are retrievable through it
