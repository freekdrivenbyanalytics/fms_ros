# skills Specification

## Purpose

Represents a skill — a named qualification an employee can hold and a product can require — used to determine which employees are qualified to perform which products' service visits.

## Requirements

### Requirement: Skill data model
The system SHALL persist each skill with a unique identifier, a name, and a soft-delete flag.

#### Scenario: Skill is persisted with required fields
- **WHEN** a skill is created with a name
- **THEN** the system persists the skill and its fields are retrievable unchanged

### Requirement: List skills
The system SHALL provide an API to retrieve the list of all skills, excluding skills marked deleted by default.

#### Scenario: Retrieve all skills
- **WHEN** a client requests the list of skills
- **THEN** the system returns all non-deleted persisted skills

#### Scenario: Deleted skill is excluded from the list
- **WHEN** a caller requests the list of skills
- **THEN** skills marked deleted are not included in the result

### Requirement: Create, update, and soft-delete a skill
The system SHALL allow a user to create a skill with a name, update its name, and soft-delete it. A soft-deleted skill SHALL NOT be permanently removed.

#### Scenario: Creating a skill
- **WHEN** a user creates a skill with a name
- **THEN** the system persists a new skill with that name

#### Scenario: Updating a skill
- **WHEN** a user updates a skill's name
- **THEN** the system persists the change, and every product or employee already associated with that skill reflects the new name

#### Scenario: Soft-deleting a skill
- **WHEN** a user soft-deletes a skill
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default skill list
