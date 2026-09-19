# Spec Delta

## ADDED Requirements

### Requirement: Route map shows a loading state while fetching
The system SHALL indicate to the user that the day-planning route map's data is being fetched, from the moment a day is selected until that day's routes have either loaded or failed to load, rather than showing an empty map area with no indication of progress.

#### Scenario: Routes are loading
- **WHEN** the day planning page has selected a day and its routes have not yet finished loading
- **THEN** the system shows a loading indicator in place of the route map

#### Scenario: Loading indicator clears once routes load
- **WHEN** a day's routes finish loading successfully
- **THEN** the system replaces the loading indicator with the route map

#### Scenario: Loading indicator clears on failure
- **WHEN** a day's routes fail to load
- **THEN** the system replaces the loading indicator with the existing error message, not a route map

### Requirement: Route map shows a legend mapping color to employee
The system SHALL display a legend alongside the day-planning route map, listing every employee shown on the map together with the color used for that employee's route.

#### Scenario: Legend lists every employee with a route
- **WHEN** the day-planning route map shows routes for one or more employees on the selected day
- **THEN** the legend lists each of those employees' names next to a color swatch matching that employee's route color on the map

#### Scenario: Legend omits an employee with no route that day
- **WHEN** an employee has no assignments on the selected day and therefore no route on the map
- **THEN** the legend does not list that employee
