# Spec Delta

## MODIFIED Requirements

### Requirement: View all employees on a single combined timeline chart
The system SHALL display a single combined timeline chart for the selected day, containing one row per employee within that one chart (not a separate chart per employee), with a timeline block for each of that employee's assignments on that day, positioned according to the assignment's planned_start and planned_end and labeled with the visit's customer name. A timeline block SHALL show its assignment's last known Resco Work Order status, when one has been pulled.

#### Scenario: Planner opens the day planning page
- **WHEN** a user opens the day planning page
- **THEN** the page renders one single timeline chart containing a row for every employee, and each employee's row shows a timeline block for every assignment whose planned_start falls on the selected day, positioned between the assignment's planned_start and planned_end and labeled with the assignment's visit's customer name

#### Scenario: Employee with no assignments on the selected day
- **WHEN** an employee has no assignment whose planned_start falls on the selected day
- **THEN** that employee's row is shown within the same combined chart with no timeline blocks

#### Scenario: A timeline block shows its Resco status
- **WHEN** the day planning chart renders a timeline block for an assignment that has a last-known Resco Work Order status
- **THEN** that block shows that status

#### Scenario: A completed visit's timeline block is not hidden
- **WHEN** the day planning chart renders a timeline block for an assignment whose Resco Work Order status is completed
- **THEN** the block is still shown on the chart, with its completed status visible - the day planning chart does not hide completed visits the way the assignment page's board does for overdue ones
