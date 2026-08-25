## MODIFIED Requirements

### Requirement: View employees and visits for assignment
The system SHALL provide a page showing the list of employees, the list of unassigned service visits, and the list of assigned service visits, with each employee card showing its region(s) and skills, and each visit card showing its customer name, region, and required skills, all expandable to show additional detail. Each of the three lists SHALL provide its own independent text search and region/skill filtering, narrowing that list without affecting the other two lists.

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
