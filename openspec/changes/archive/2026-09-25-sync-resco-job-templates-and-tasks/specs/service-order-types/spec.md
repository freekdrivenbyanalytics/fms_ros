# Spec Delta

## ADDED Requirements

### Requirement: Initial tasks for existing caretaker service order types
The system SHALL provide a one-time initial-data backfill that associates `generell inspeksjon` with the existing `Generelle vaktmestertjenester` service order type and associates the same reusable task followed by `lett snømåking` with the existing `Vaktmestertjenester (vinter)` service order type. Initial task descriptions and estimated durations SHALL be unset. The backfill SHALL preserve unrelated data, SHALL NOT create replacement service order types or perform remote writes, and SHALL NOT duplicate tasks/associations or reset subsequent administrator edits when repeated.

#### Scenario: Populate the existing types
- **WHEN** the initial-data backfill runs with both existing types uniquely identified and no task data yet populated
- **THEN** the general type has `generell inspeksjon` and the winter type has that same task followed by `lett snømåking`, with exactly two reusable task records created

#### Scenario: Repeat the initial-data backfill
- **WHEN** the completed backfill is invoked again, including after an administrator changes task associations
- **THEN** it creates no duplicate tasks or associations and preserves the administrator's changes

#### Scenario: Existing type cannot be identified
- **WHEN** either target type is missing or its name matches multiple existing types
- **THEN** the backfill reports the unresolved match without partially populating data or creating replacement types

### Requirement: Service order types have ordered task associations
The system SHALL allow administrators to associate zero or more active tasks with each service order type and specify their order. A task SHALL be reusable across types and occur at most once within a type. Task edits SHALL be reflected by every type using that task. Unlinking a task from one type SHALL preserve the task and its links to other types. Type/product associations SHALL remain independent of task associations.

#### Scenario: Reuse and order tasks
- **WHEN** an administrator assigns the same task to two types and changes its position within one type
- **THEN** both types retain the shared task and each type's order is stored independently

#### Scenario: Unlink a task
- **WHEN** an administrator removes a task from a type
- **THEN** only that association stops contributing to the type's template and neither the task nor its other associations are deleted

#### Scenario: Reject invalid associations
- **WHEN** a type's task list includes duplicate, missing or deleted task IDs
- **THEN** the system rejects the list without partially changing associations

### Requirement: Service order types retain Resco sync identity
Each service order type SHALL retain the identity of its corresponding Resco job template once synced. Each type/task association SHALL retain enough identity to update or retire the same remote template task on retries and membership changes. Local edits SHALL succeed even if the downstream sync fails and SHALL surface the failure for retry.

#### Scenario: Rename a synced type
- **WHEN** an administrator renames a type whose template already exists
- **THEN** its remote template is updated using its remembered identity without creating a replacement

#### Scenario: Resco is unavailable
- **WHEN** a type or task-association edit succeeds locally but its Resco sync fails
- **THEN** the local changes remain saved and the response reports that Resco needs a retry
