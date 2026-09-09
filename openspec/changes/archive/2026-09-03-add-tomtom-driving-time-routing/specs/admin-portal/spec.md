## ADDED Requirements

### Requirement: Compute driving times for a region from the Admin Portal
The system SHALL let a user, from the Admin Portal's Regions view, trigger driving-time computation for a region, alongside the existing "re-assign regions" action. While computation is in progress the system SHALL indicate that it is running, and SHALL show a result or error message once it completes.

#### Scenario: Triggering driving-time computation
- **WHEN** a user clicks the "Compute driving times" action in the Admin Portal's Regions view for a region
- **THEN** the system triggers that region's driving-time computation and, once it completes, shows a result message

#### Scenario: Computation in progress is indicated
- **WHEN** a user triggers driving-time computation and it has not yet completed
- **THEN** the system shows that computation is in progress and disables re-triggering it until it finishes

#### Scenario: A failed computation is reported
- **WHEN** driving-time computation for a region fails
- **THEN** the system shows an error message rather than silently discarding the failure
