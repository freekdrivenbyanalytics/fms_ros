# skills Specification

## Purpose

Represents named qualifications employees can hold and contracts can require, used to describe what a service visit needs and who is qualified to do it.

## Requirements

### Requirement: Skill data model
The system SHALL persist each skill with a unique identifier and a name.

#### Scenario: Skill is persisted with required fields
- **WHEN** a skill record is created with id and name
- **THEN** the system persists the skill and both fields are retrievable unchanged
