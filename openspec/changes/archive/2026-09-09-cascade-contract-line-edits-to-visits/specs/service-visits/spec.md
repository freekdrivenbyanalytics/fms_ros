## ADDED Requirements

### Requirement: Updating a contract line regenerates its not-yet-started visits
The system SHALL, when a contract line is updated, remove every one of that line's service visits that does not have a started assignment (an assignment whose planned_start has already passed, per the assignments capability's definition) — this includes unassigned visits and assigned-but-not-started visits, regardless of whether the assignment is pinned — and generate the line's future visits from its current (just-saved) start_date, interval_days, end_date, and required products. The anchor for generation SHALL be the requested_date of the line's most recent visit with a started assignment, if one exists; otherwise the line's start_date, subject to the past-start_date rollover described below. Visits with a started assignment SHALL NOT be removed, unassigned, or otherwise altered by this operation.

#### Scenario: Not-yet-started visits are removed and regenerated
- **WHEN** a contract line is updated and it has one or more service visits with no started assignment
- **THEN** the system removes those visits (and any not-yet-started assignment on them, including pinned ones) and generates new visits for the line's future from its updated terms

#### Scenario: Started visits are left untouched
- **WHEN** a contract line is updated and it has a service visit with a started assignment
- **THEN** that visit and its assignment are unchanged, and it counts as history the new visits are generated after rather than something regeneration can remove

#### Scenario: Regeneration anchors on the last started visit
- **WHEN** a contract line is updated and its most recent visit with a started assignment was requested on a given date
- **THEN** the newly generated visits start from the next occurrence after that date, spaced by the line's (possibly updated) interval_days, rather than from today

#### Scenario: Regeneration anchors on start_date when nothing has started yet
- **WHEN** a contract line is updated, none of its visits have a started assignment, and the line's start_date is today or in the future
- **THEN** the newly generated visits begin at the line's start_date, exactly as they would for a newly created line

#### Scenario: A past start_date with nothing started yet rolls its first occurrence to today
- **WHEN** a contract line is updated, none of its visits have a started assignment, the line's start_date is before today, and the line's end_date (or open-ended 90-day horizon) is today or later
- **THEN** the first newly generated visit is requested for today, and every subsequent visit falls on the cadence implied by the line's original start_date and interval_days (not a cadence restarted from today) — so occurrences between the original start_date and today are collapsed into that one visit today rather than generated as a backlog of overdue visits

#### Scenario: An already-elapsed line with nothing started yet regenerates no visits
- **WHEN** a contract line is updated, none of its visits have a started assignment, and the line's end_date (or open-ended 90-day horizon) is before today
- **THEN** the system generates no new visits for the line, rather than rolling one stray visit to today past the line's own end

#### Scenario: Regenerated visits reflect the line's current required products
- **WHEN** a contract line's visits are regenerated after an update that changed its required products
- **THEN** the newly generated visits' required products (read through the contract line) reflect the new set, since visits do not store their own copy

#### Scenario: Regeneration respects the line's (possibly new) end date or open-ended horizon
- **WHEN** a contract line is updated with a bounded end_date, or with no end_date
- **THEN** the newly generated visits extend up to and including that end_date, or up to 90 days ahead of today if the line has no end_date, matching the same horizon rule used when a contract line is first created
