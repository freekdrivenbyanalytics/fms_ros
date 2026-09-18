# service-visits Specification

## Purpose

Represents customer service visits requested for scheduling, tracked through an unassigned/assigned lifecycle so planners can see what still needs an employee.

## Requirements

### Requirement: Service visit data model
The system SHALL persist each service visit with a unique identifier, the contract line it was generated from, requested date, and a status; duration, product requirements, required skills, and priority are read through the contract line.

#### Scenario: Service visit is persisted with required fields
- **WHEN** a service visit is created with id, contract_line_id, and requested_date
- **THEN** the system persists the service visit and all fields are retrievable unchanged, with customer name, address, region, duration, required products, required skills, and priority available through the contract line

### Requirement: New service visits start unassigned
A newly created service visit SHALL have status `unassigned` until an assignment is created for it.

#### Scenario: New visit has unassigned status
- **WHEN** a service visit is created and no assignment exists for it
- **THEN** its status is `unassigned`

### Requirement: List service visits by assignment status
The system SHALL provide an API to retrieve service visits with their status, their contract line's customer location (customer name, address, region), duration, required products, and required skills (the union of the skills required by those products), so unassigned visits and assigned visits can be distinguished, located, and matched to a qualified employee. The API SHALL accept optional start-date and end-date filters that restrict the returned visits to those whose requested_date falls within the given range (inclusive); omitting either bound leaves that side of the range open.

#### Scenario: Retrieve visits with status
- **WHEN** a client requests the list of service visits
- **THEN** the system returns every visit together with its status of either `unassigned` or `assigned`, and the customer name, address, region, duration, required products, and required skills of the contract line it was generated from

#### Scenario: Retrieve visits within a date range
- **WHEN** a client requests the list of service visits with a start-date and/or end-date filter
- **THEN** the system returns only visits whose requested_date falls within the given range, applying only the bounds that were provided

#### Scenario: No date filter returns every visit
- **WHEN** a client requests the list of service visits with no start-date or end-date filter
- **THEN** the system returns every visit regardless of requested_date, unchanged from today's behavior

### Requirement: Creating a contract line generates its service visits
The system SHALL, when a contract line is created, generate one unassigned service visit for the contract line's start_date and for every subsequent occurrence spaced by the line's interval unit and count (stepping by real calendar weeks, months, or quarters), up to and including the contract line's end_date if it has one, or up to 90 days after start_date if it has no end_date. Each generated visit SHALL be linked to that contract line.

#### Scenario: Generating visits for a bounded contract line
- **WHEN** a contract line is created with a start_date, interval unit and count, and an end_date
- **THEN** the system creates one unassigned service visit for start_date and for every occurrence spaced by the interval unit and count thereafter, up to and including end_date

#### Scenario: Generating visits for an open-ended contract line
- **WHEN** a contract line is created with a start_date and interval unit and count but no end_date
- **THEN** the system creates one unassigned service visit for start_date and for every occurrence spaced by the interval unit and count thereafter, up to 90 days after start_date

#### Scenario: A monthly or quarterly interval steps by calendar months, not a fixed day count
- **WHEN** a contract line's interval unit is `month` or `quarter`
- **THEN** each generated occurrence falls on the same day-of-month as start_date, that many calendar months later (clamped to the shorter month's last day when start_date's day-of-month doesn't exist there, for example January 31 stepping by one month lands on February 28 or 29)

#### Scenario: Generated visits are linked to their contract line
- **WHEN** a contract line's service visits are generated
- **THEN** each generated visit's contract_line_id refers to that contract line, and the visits are retrievable through it

### Requirement: Open-ended contract lines' visit horizon can be topped up on demand
The system SHALL let a user trigger extending every open-ended (no `end_date`) contract line's generated service visits so each line's furthest generated occurrence reaches 90 days ahead of today. Extending SHALL generate only the occurrences between a line's current furthest generated occurrence and the new horizon, spaced by the line's interval unit and count — it SHALL NOT duplicate or regenerate visits that already exist. A contract line whose furthest generated occurrence is already at or beyond the horizon SHALL be left unchanged. Contract lines with an `end_date` SHALL NOT be affected by this operation.

#### Scenario: Topping up a line whose horizon has fallen behind
- **WHEN** the extend-visits operation runs and an open-ended contract line's furthest generated occurrence is less than 90 days ahead of today
- **THEN** the system generates the missing occurrences, spaced by the line's interval unit and count, from just after the line's furthest existing occurrence up to 90 days ahead of today

#### Scenario: A line already at or beyond the horizon is untouched
- **WHEN** the extend-visits operation runs and an open-ended contract line's furthest generated occurrence is already 90 or more days ahead of today
- **THEN** the system generates no additional visits for that line

#### Scenario: Extending never duplicates existing visits
- **WHEN** the extend-visits operation runs more than once without any intervening passage of time past the horizon
- **THEN** the second run generates no additional visits for lines the first run already brought up to the horizon

#### Scenario: Bounded contract lines are not extended
- **WHEN** the extend-visits operation runs
- **THEN** contract lines with an end_date are left unchanged regardless of how close their end_date is

### Requirement: Updating a contract line regenerates its not-yet-started visits
The system SHALL, when a contract line is updated, remove every one of that line's service visits that does not have a started assignment (an assignment whose planned_start has already passed, per the assignments capability's definition) — this includes unassigned visits and assigned-but-not-started visits, regardless of whether the assignment is pinned — and generate the line's future visits from its current (just-saved) start_date, interval unit and count, end_date, and required products. The anchor for generation SHALL be the requested_date of the line's most recent visit with a started assignment, if one exists; otherwise the line's start_date, subject to the past-start_date rollover described below. Visits with a started assignment SHALL NOT be removed, unassigned, or otherwise altered by this operation.

#### Scenario: Not-yet-started visits are removed and regenerated
- **WHEN** a contract line is updated and it has one or more service visits with no started assignment
- **THEN** the system removes those visits (and any not-yet-started assignment on them, including pinned ones) and generates new visits for the line's future from its updated terms

#### Scenario: Started visits are left untouched
- **WHEN** a contract line is updated and it has a service visit with a started assignment
- **THEN** that visit and its assignment are unchanged, and it counts as history the new visits are generated after rather than something regeneration can remove

#### Scenario: Regeneration anchors on the last started visit
- **WHEN** a contract line is updated and its most recent visit with a started assignment was requested on a given date
- **THEN** the newly generated visits start from the next occurrence after that date, spaced by the line's (possibly updated) interval unit and count, rather than from today

#### Scenario: Regeneration anchors on start_date when nothing has started yet
- **WHEN** a contract line is updated, none of its visits have a started assignment, and the line's start_date is today or in the future
- **THEN** the newly generated visits begin at the line's start_date, exactly as they would for a newly created line

#### Scenario: A past start_date with nothing started yet rolls its first occurrence to today
- **WHEN** a contract line is updated, none of its visits have a started assignment, the line's start_date is before today, and the line's end_date (or open-ended 90-day horizon) is today or later
- **THEN** the first newly generated visit is requested for today, and every subsequent visit falls on the cadence implied by the line's original start_date and interval unit/count (not a cadence restarted from today) — so occurrences between the original start_date and today are collapsed into that one visit today rather than generated as a backlog of overdue visits

#### Scenario: An already-elapsed line with nothing started yet regenerates no visits
- **WHEN** a contract line is updated, none of its visits have a started assignment, and the line's end_date (or open-ended 90-day horizon) is before today
- **THEN** the system generates no new visits for the line, rather than rolling one stray visit to today past the line's own end

#### Scenario: Regenerated visits reflect the line's current required products
- **WHEN** a contract line's visits are regenerated after an update that changed its required products
- **THEN** the newly generated visits' required products (read through the contract line) reflect the new set, since visits do not store their own copy

#### Scenario: Regeneration respects the line's (possibly new) end date or open-ended horizon
- **WHEN** a contract line is updated with a bounded end_date, or with no end_date
- **THEN** the newly generated visits extend up to and including that end_date, or up to 90 days ahead of today if the line has no end_date, matching the same horizon rule used when a contract line is first created
