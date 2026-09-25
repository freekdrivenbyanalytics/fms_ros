# tasks Specification

## Purpose

Provides independent task master data describing work to perform, reusable through service order types and their corresponding Resco job templates.

## Requirements

### Requirement: Task master data
The system SHALL persist each task with a portal-assigned identifier, required nonblank name, optional description, optional estimated duration in whole minutes and a soft-delete flag. An estimated duration, when supplied, SHALL be positive. Tasks SHALL be independent of products; creating or syncing a product SHALL NOT automatically create a task.

#### Scenario: Create and update a task
- **WHEN** an administrator creates or updates a task with valid values
- **THEN** the task is persisted locally and its fields are retrievable with the same identifier on update

#### Scenario: Invalid task values
- **WHEN** a task write supplies a blank name or a nonpositive estimated duration
- **THEN** the system rejects the write without changing the task

### Requirement: Task access and soft deletion
The system SHALL provide admin-only task list, create, update and soft-delete operations. Default lists SHALL exclude deleted tasks. Deleting a task SHALL remove it from the effective task lists of all linked service order types without destroying its identity or previously instantiated work-order task history. Missing or deleted task IDs SHALL NOT be accepted in new associations.

#### Scenario: Delete a linked task
- **WHEN** an administrator soft-deletes a task linked to two service order types
- **THEN** it disappears from both effective task lists and the default task list while its identity and historical work-order tasks remain intact

#### Scenario: Unauthorized task write
- **WHEN** an unauthenticated or non-admin caller attempts task administration
- **THEN** the request is rejected without a local or remote mutation
