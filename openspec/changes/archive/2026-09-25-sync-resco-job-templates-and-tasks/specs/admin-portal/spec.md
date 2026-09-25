# Spec Delta

## ADDED Requirements

### Requirement: Products page provides explicit Resco synchronization
The Admin Portal Products page SHALL provide a `Sync to Resco` button separate from the Tripletex sync action. It SHALL push all active portal products, display a pending state preventing duplicate clicks, report created/updated/skipped/failed counts and per-product errors, and refresh displayed product data afterwards. Product creation/editing SHALL continue to trigger automatic Resco sync and display any sync warning without presenting a successful local save as failed. Opening the page SHALL NOT trigger synchronization.

#### Scenario: Manually sync products
- **WHEN** an administrator clicks `Sync to Resco` on the Products page
- **THEN** active products are pushed and results are displayed, including individual failures, while archived/deleted products are excluded

#### Scenario: Automatic product sync fails
- **WHEN** a product create or edit succeeds locally but its automatic Resco sync returns a failure
- **THEN** the page shows the saved product and a warning, and the manual button allows retry

### Requirement: Tasks administration
The Admin Portal SHALL provide task list and detail views, create/edit controls for task name, description and estimated duration, and a soft-delete control. Task details SHALL show which active service order types use the task. A deleted task SHALL no longer appear in default lists or selection controls.

#### Scenario: Manage a task
- **WHEN** an administrator creates a task, edits its description and opens its detail view
- **THEN** the saved fields and linked service order types are displayed

### Requirement: Edit service order type tasks and sync templates
The Service Order Types detail view SHALL display and edit its ordered task list independently of its existing product list. The view SHALL display its remembered Resco template identity and transient sync warnings. Administrators SHALL be able to explicitly bootstrap or retry template/task sync and see per-type failures and created/updated/skipped/failed counts. Opening the view SHALL NOT trigger remote sync.

#### Scenario: Select and reorder tasks
- **WHEN** an administrator selects existing tasks and reorders them on a type
- **THEN** the saved order is shown on the type without changing which products belong to it

#### Scenario: Retry failed template sync
- **WHEN** an administrator invokes Sync to Resco after a previous failure
- **THEN** the portal retries template/task sync, reports the results and refreshes displayed identities and task information

#### Scenario: Local save succeeds while remote sync fails
- **WHEN** a type or task save returns a sync warning
- **THEN** the portal displays the saved data and warning without presenting the local write as failed
