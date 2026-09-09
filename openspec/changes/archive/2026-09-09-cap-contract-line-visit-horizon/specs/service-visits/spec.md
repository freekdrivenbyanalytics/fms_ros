## MODIFIED Requirements

### Requirement: Creating a contract line generates its service visits
The system SHALL, when a contract line is created, generate one unassigned service visit for the contract line's start_date and for every subsequent occurrence spaced interval_days apart, up to and including the contract line's end_date if it has one, or up to 90 days after start_date if it has no end_date. Each generated visit SHALL be linked to that contract line.

#### Scenario: Generating visits for a bounded contract line
- **WHEN** a contract line is created with a start_date, interval_days, and an end_date
- **THEN** the system creates one unassigned service visit for start_date and for every occurrence interval_days apart thereafter, up to and including end_date

#### Scenario: Generating visits for an open-ended contract line
- **WHEN** a contract line is created with a start_date and interval_days but no end_date
- **THEN** the system creates one unassigned service visit for start_date and for every occurrence interval_days apart thereafter, up to 90 days after start_date

#### Scenario: Generated visits are linked to their contract line
- **WHEN** a contract line's service visits are generated
- **THEN** each generated visit's contract_line_id refers to that contract line, and the visits are retrievable through it

## ADDED Requirements

### Requirement: Open-ended contract lines' visit horizon can be topped up on demand
The system SHALL let a user trigger extending every open-ended (no `end_date`) contract line's generated service visits so each line's furthest generated occurrence reaches 90 days ahead of today. Extending SHALL generate only the occurrences between a line's current furthest generated occurrence and the new horizon — it SHALL NOT duplicate or regenerate visits that already exist. A contract line whose furthest generated occurrence is already at or beyond the horizon SHALL be left unchanged. Contract lines with an `end_date` SHALL NOT be affected by this operation.

#### Scenario: Topping up a line whose horizon has fallen behind
- **WHEN** the extend-visits operation runs and an open-ended contract line's furthest generated occurrence is less than 90 days ahead of today
- **THEN** the system generates the missing occurrences, spaced interval_days apart, from just after the line's furthest existing occurrence up to 90 days ahead of today

#### Scenario: A line already at or beyond the horizon is untouched
- **WHEN** the extend-visits operation runs and an open-ended contract line's furthest generated occurrence is already 90 or more days ahead of today
- **THEN** the system generates no additional visits for that line

#### Scenario: Extending never duplicates existing visits
- **WHEN** the extend-visits operation runs more than once without any intervening passage of time past the horizon
- **THEN** the second run generates no additional visits for lines the first run already brought up to the horizon

#### Scenario: Bounded contract lines are not extended
- **WHEN** the extend-visits operation runs
- **THEN** contract lines with an end_date are left unchanged regardless of how close their end_date is
