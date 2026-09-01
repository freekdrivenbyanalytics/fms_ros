## MODIFIED Requirements

### Requirement: View employees and visits for assignment
The system SHALL provide a page showing the list of employees, the list of unassigned service visits, and the list of assigned service visits, with each employee card showing its region(s) and skills, and each visit card showing its customer name, region, and required skills, all expandable to show additional detail. Each of the three lists SHALL provide its own independent text search and region/skill filtering, narrowing that list without affecting the other two lists. Each assigned visit card SHALL show whether its assignment is pinned, and offer controls to unassign it and to pin or unpin it. The unassigned and assigned visit lists SHALL share a single date-range control: by default it includes every visit requested before today (no lower bound) through seven days from today; a "This Week" preset moves the upper bound to the end of the current calendar week, and a "4 Weeks" preset moves it to 28 days from today; in every case, visits requested before today remain included regardless of which upper bound is selected.

#### Scenario: Planner views the assignment page
- **WHEN** a user opens the assignment page
- **THEN** the page displays all employees, all unassigned service visits, and all assigned service visits, each employee showing its region(s) and skills, and each visit showing its customer name, region, and required skills

#### Scenario: Planner expands a card for more detail
- **WHEN** a user clicks an employee or service visit card
- **THEN** the card expands to show an info box with additional detail not shown on the collapsed card (at least the region(s) for an employee; at least the address and GPS coordinates for a service visit, whether unassigned or assigned)

#### Scenario: Planner searches a list by name or address
- **WHEN** a user types text into a list's search box
- **THEN** that list shows only the employees or visits whose name (employee name, or visit's customer name) or, for a visit, location address, contains the search text, and the other two lists are unaffected

#### Scenario: Planner filters a list by region and skill
- **WHEN** a user selects one or more regions and/or one or more skills in a list's filters
- **THEN** that list shows only the employees or visits that have at least one of the selected regions (if any region is selected) and at least one of the selected skills (if any skill is selected), and the other two lists are unaffected

#### Scenario: Search and filters combine within a list
- **WHEN** a user has both entered search text and selected region/skill filters on the same list
- **THEN** that list shows only the employees or visits matching the search text and satisfying the selected filters

#### Scenario: No search text and no filters selected
- **WHEN** a list's search box is empty and no region or skill filters are selected
- **THEN** that list shows every employee or visit it would show without search or filtering

#### Scenario: Assigned visit cards show pin state and actions
- **WHEN** a user views the assigned service visits list
- **THEN** each assigned visit card indicates whether it is pinned, and offers an "Unassign" action and a pin/unpin action

#### Scenario: Default date range shows overdue and near-term visits
- **WHEN** a user opens the assignment page without changing the date-range control
- **THEN** both the unassigned and assigned visit lists show only visits requested before today or within the next seven days

#### Scenario: "This Week" preset extends the range to the end of the current week
- **WHEN** a user selects the "This Week" preset
- **THEN** both visit lists show visits requested before today or up to the end of the current calendar week

#### Scenario: "4 Weeks" preset extends the range further out
- **WHEN** a user selects the "4 Weeks" preset
- **THEN** both visit lists show visits requested before today or up to 28 days from today

#### Scenario: Overdue visits are never hidden by the date range
- **WHEN** any date-range selection is active, whether the default or a preset
- **THEN** visits requested before today remain included in both visit lists regardless of the selected upper bound
