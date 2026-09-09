## MODIFIED Requirements

### Requirement: View full assignment detail from a timeline block
The system SHALL let a user view an assignment's full service visit detail — the customer, address, region, and required products — from its timeline block on the day planning chart.

#### Scenario: Planner expands a timeline block
- **WHEN** a user expands a timeline block
- **THEN** the system shows the visit's customer name, address, region, and required products, alongside the assignment's planned start and end times

## REMOVED Requirements

### Requirement: View employee skills on the chart
**Reason**: Skills are replaced by Tripletex-sourced products; see "View employee products on the chart" below.
**Migration**: None needed — the same row-label badge shape carries over to products.

## ADDED Requirements

### Requirement: View employee products on the chart
The system SHALL show, on each employee's row label in the day planning chart, the products that employee possesses.

#### Scenario: Planner views an employee's row
- **WHEN** the day planning chart renders an employee's row
- **THEN** the row label shows the employee's name and the products that employee possesses
