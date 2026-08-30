## ADDED Requirements

### Requirement: An assignment locks automatically once it has started
The system SHALL treat an assignment as pinned — regardless of its stored pin flag — once its planned start time has passed. This lock is based on elapsed time, not the stored flag, and cannot be removed by unpinning.

#### Scenario: An already-started assignment is shown as pinned
- **WHEN** a user views an assignment whose planned start time has already passed
- **THEN** the system shows that assignment as pinned, even if it was never manually pinned

#### Scenario: Unpinning an already-started assignment does not unlock it
- **WHEN** a user unpins an assignment whose planned start time has already passed
- **THEN** the system updates the stored pin flag, but the assignment continues to be shown as pinned and remains excluded from schedule runs
