## Purpose

Lets the team quickly make an already-seeded demo or test dataset usable again — refreshing visit dates and clearing assignments — without the cost and risk of the full Tripletex-connected reset-and-reseed.

## ADDED Requirements

### Requirement: Refreshing the demo schedule shifts visit dates to start from today
The system SHALL let a user trigger an action that shifts every service visit's requested date forward by the same number of days, chosen so that the earliest requested date across all service visits becomes today, preserving each visit's spacing relative to every other visit. If the earliest requested date is already today or later, no visit's requested date SHALL be changed.

#### Scenario: Visit dates are shifted forward when the earliest is in the past
- **WHEN** a user triggers the schedule refresh and the earliest service visit requested date is before today
- **THEN** every service visit's requested date is shifted forward by the same number of days, such that the previously-earliest visit's requested date becomes today, and the interval between every pair of visits' requested dates is unchanged

#### Scenario: No shift when nothing is in the past
- **WHEN** a user triggers the schedule refresh and the earliest service visit requested date is already today or a future date
- **THEN** no service visit's requested date is changed

### Requirement: Refreshing the demo schedule clears all assignments
The system SHALL, as part of the same action, remove every existing assignment — including pinned ones — and set every affected service visit's status back to unassigned.

#### Scenario: All assignments are removed
- **WHEN** a user triggers the schedule refresh
- **THEN** every previously existing assignment, pinned or not, is removed, and every service visit that had an assignment is now unassigned

### Requirement: Refreshing the demo schedule makes no Tripletex API calls
The system SHALL perform the schedule refresh entirely against the local database, making no calls to Tripletex and making no changes to customers, customer locations, contracts, contract lines, or employees.

#### Scenario: Refreshing the schedule does not touch Tripletex or other entities
- **WHEN** a user triggers the schedule refresh
- **THEN** no Tripletex API call is made, and no customer, customer location, contract, contract line, or employee record is created, modified, or deleted
