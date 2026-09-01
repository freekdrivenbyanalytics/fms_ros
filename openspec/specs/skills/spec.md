# skills Specification

## Purpose

Represents named qualifications employees can hold and contracts can require, used to describe what a service visit needs and who is qualified to do it.

## Requirements

### Requirement: Skill data model
The system SHALL persist each skill with a unique identifier, a name, and a soft-delete flag.

#### Scenario: Skill is persisted with required fields
- **WHEN** a skill record is created with id and name
- **THEN** the system persists the skill and both fields are retrievable unchanged

### Requirement: Create, update, and soft-delete a skill
The system SHALL allow a user to create a skill with a name, update its name, and soft-delete it. A soft-deleted skill SHALL NOT be permanently removed.

#### Scenario: Creating a skill
- **WHEN** a user creates a skill with a name
- **THEN** the system persists a new skill with that name

#### Scenario: Updating a skill's name
- **WHEN** a user updates a skill's name
- **THEN** the system persists the change

#### Scenario: Soft-deleting a skill
- **WHEN** a user soft-deletes a skill
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default skill list, while any employees or contract lines still referencing it remain unaffected

### Requirement: Deleted skills are hidden by default
The system SHALL exclude skills marked deleted from the skill list returned to callers by default.

#### Scenario: Deleted skill is excluded from the list
- **WHEN** a caller requests the list of skills
- **THEN** skills marked deleted are not included in the result
