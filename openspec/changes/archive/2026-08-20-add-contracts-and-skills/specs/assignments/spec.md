## MODIFIED Requirements

### Requirement: View employees and visits for assignment
The system SHALL provide a page showing the list of employees, the list of unassigned service visits, and the list of assigned service visits, with each employee card showing its region(s) and skills, and each visit card showing its customer name, region, and required skills, all expandable to show additional detail.

#### Scenario: Planner views the assignment page
- **WHEN** a user opens the assignment page
- **THEN** the page displays all employees, all unassigned service visits, and all assigned service visits, each employee showing its region(s) and skills, and each visit showing its customer name, region, and required skills

#### Scenario: Planner expands a card for more detail
- **WHEN** a user clicks an employee or service visit card
- **THEN** the card expands to show an info box with additional detail not shown on the collapsed card (at least the region(s) for an employee; at least the address and GPS coordinates for a service visit, whether unassigned or assigned)
