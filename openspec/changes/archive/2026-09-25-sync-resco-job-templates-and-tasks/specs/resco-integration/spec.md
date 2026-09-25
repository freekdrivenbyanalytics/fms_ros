# Spec Delta

## ADDED Requirements

### Requirement: Product synchronization supports explicit admin retry
An admin-only `POST /products/sync-resco` operation SHALL push all products with neither archived nor delete_flag set, using the same identity-based create/update logic as automatic product create/edit sync. A remembered Resco Product ID SHALL select the record to update with the current mapped name and product number; absent that ID, sync SHALL create the record and persist the returned ID. Failures SHALL preserve local product data and remembered remote IDs, SHALL NOT trigger replacement creation for a failed update, and SHALL be reported per product without stopping the remaining batch. Automatic sync failures SHALL also be surfaced as local-save warnings. Product/type links SHALL NOT be exported.

#### Scenario: Retry existing and new products
- **WHEN** an administrator syncs a batch containing a product with a remembered Resco ID and a product without one
- **THEN** the first remote product is updated in place and the second is created with its returned ID remembered for subsequent updates

#### Scenario: One product fails during a batch
- **WHEN** updating one product fails
- **THEN** its local data and remote ID remain intact, no replacement product is created, remaining products are processed, and the summary reports the failure

#### Scenario: Non-admin attempts product sync
- **WHEN** an unauthenticated or non-admin caller invokes the product sync operation
- **THEN** access is denied without remote writes

### Requirement: Service order types sync as job templates with tasks
Each active service order type SHALL map to one Resco job template named after the type. Its active linked tasks SHALL be synced with their names, descriptions, optional estimated durations, order and template associations. A reusable portal task SHALL have a distinct remote task instance under each linked template. Product master-data sync SHALL remain available, but this mapping SHALL NOT create template-product associations or derive tasks from products.

#### Scenario: Sync a type and its task list
- **WHEN** a type with two linked tasks is synced
- **THEN** Resco contains one corresponding template and two ordered task children linked to it, with no product links added to the template

#### Scenario: Reusable task belongs to two templates
- **WHEN** a task is linked to two service order types
- **THEN** each corresponding template has its own linked remote task instance carrying the shared task's current fields

### Requirement: Template synchronization follows local edits and supports retry
The system SHALL attempt template sync after a type is created or renamed or its task associations change, and SHALL sync affected templates after a linked task is edited or deleted. Unlinked/deleted tasks SHALL be retired from future template use without hard-deleting remote records or changing previously instantiated work-order tasks. A deleted type SHALL not be selected for new jobs. Explicit admin bootstrap SHALL process existing types and pending retirements. No sync SHALL run at startup. Failures SHALL preserve local writes, report per-item errors and retain successful remote identities for repeatable retries.

#### Scenario: Retry a partially synced template
- **WHEN** the template was created but one task failed and sync is retried
- **THEN** the same template and successful task records are reused while missing work is completed without duplicates

#### Scenario: Unlink or delete a task
- **WHEN** a previously synced task is unlinked or soft-deleted
- **THEN** the affected remote template task is retired so future applications exclude it, with historical Work Order tasks unchanged

#### Scenario: Shared task update has a partial failure
- **WHEN** updating a shared task succeeds for one template and fails for another
- **THEN** the portal preserves the local update, reports the failed template and can retry it without duplicating successful records

### Requirement: Work Orders apply every selected job template
When syncing a new assignment, the system SHALL derive distinct active service order types from the visit's required products and apply each corresponding synced template exactly once to the Work Order. The portal SHALL explicitly create Work Order tasks through the API using the service order type's active ordered tasks, linked to the corresponding applied job and Work Order. The job name SHALL match the service order type/job template name at creation. Stable remembered identities SHALL prevent duplicate jobs/tasks on retries, and later synchronization SHALL preserve task contents and progress. Each applied template SHALL contribute its full active ordered task list. Products without an active type SHALL contribute no template. Template failures SHALL be reported without rolling back the local assignment or losing created remote identities.

#### Scenario: Multiple products share a type
- **WHEN** a visit includes two products belonging to one type
- **THEN** one job for that template is applied to its Work Order and the portal creates that type's tasks once through the API

#### Scenario: Multiple types on one visit
- **WHEN** a visit's products refer to two active service order types
- **THEN** the same Work Order receives both jobs and their respective template task lists

#### Scenario: Product has no service order type
- **WHEN** a required product has no active type
- **THEN** it remains eligible for Work Order product sync without an invented job template or task

#### Scenario: Template changes after Work Order creation
- **WHEN** a template is edited after its tasks were instantiated on a Work Order
- **THEN** normal rescheduling does not reapply the template or overwrite existing task contents, completion or progress

### Requirement: Work Orders include their selected products
The assignment sync SHALL ensure that each distinct active required product is represented once as a Resco Work Order product line linked to the corresponding Resco Product and Work Order. A typed product SHALL also link to the corresponding applied job where supported by the verified Resco mapping. Products SHALL be selected from the visit, not from every product belonging to its service order type. Product lines SHALL NOT create template-product links or act as the source of template tasks. Repeated sync SHALL reuse existing lines and preserve remote usage and pricing values.

#### Scenario: A type has more products than the visit selects
- **WHEN** a visit selects one of three products belonging to a type
- **THEN** the Work Order gets that one product line and the type's job template with its linked tasks, not the other two products

#### Scenario: Product sync fails
- **WHEN** a required product cannot be created or linked in Resco
- **THEN** the local assignment remains saved and sync reports the missing line as incomplete while retaining successful product, job and Work Order identities for retry

### Requirement: Work Orders and job templates use a NOK price list
The system SHALL reuse the active NOK currency configured in Resco and resolve or create an active price list linked to that currency. Currency matching SHALL use ISO currency code and price-list matching SHALL validate its currency rather than relying on its name. Every newly synced portal Work Order and job template SHALL receive a valid NOK price list and matching currency. A missing/inactive NOK currency or ambiguous price-list selection SHALL produce an actionable sync failure rather than an arbitrary currency, rate or price list. Existing remote prices, configured currency exchange rates and the organization's base currency SHALL NOT be changed by setup.

#### Scenario: Reuse existing NOK setup
- **WHEN** a suitable NOK currency and configured or unambiguous active NOK price list exist
- **THEN** sync reuses their IDs and creates no duplicate setup records

#### Scenario: NOK price list is missing
- **WHEN** the configured NOK currency exists but no suitable NOK price list exists
- **THEN** sync creates one active NOK price list and reuses it for the template and Work Order

#### Scenario: Configured NOK currency is unavailable
- **WHEN** the NOK currency is absent or inactive
- **THEN** sync reports the missing prerequisite without creating a currency, changing rates or failing the local business write

### Requirement: Existing portal Work Orders can acquire missing job and pricing data
An explicit admin operation SHALL preview and apply missing job-template applications, selected product lines and NOK price-list/currency fields to selected remembered portal Work Orders. It SHALL leave unrelated Resco records untouched, preserve Work Order/schedule IDs and planned times, and skip progressed or conflicting records rather than overwrite field work or non-NOK commercial data. Retrying after partial success SHALL not duplicate jobs, products or API-created tasks.

#### Scenario: Catch up an eligible existing Work Order
- **WHEN** a selected portal Work Order is still Scheduled, has no field progress and lacks these additions
- **THEN** catch-up adds the missing fields, jobs and product lines in place and the portal creates the missing tasks through the API

#### Scenario: Field work has progressed or commercial data conflicts
- **WHEN** an existing Work Order has progressed or already carries incompatible pricing data
- **THEN** catch-up skips it with a reason without changing its jobs, task progress, product values or currency

### Requirement: Product masters carry service classification and NOK defaults
Automatic and explicit product synchronization SHALL set Resco Product isservice to true for TJN and false for PRD and bind the validated active NOK currency and NOK default price list. Existing remembered products SHALL be corrected in place. Setup failures SHALL preserve local writes and remote identity and report a retryable failure. Product prices, costs, units and currency exchange rates SHALL NOT be supplied or changed by this mapping. Product lines SHALL continue to be sent directly to Work Orders without template-product associations.

#### Scenario: Correct a previously synced service product
- **WHEN** TJN10002 is synced with a remembered remote identity and missing service/pricing defaults
- **THEN** the same Product receives isservice true, NOK currency and the NOK default price list without replacement creation

#### Scenario: Sync a physical product
- **WHEN** a PRD product is created or updated in Resco
- **THEN** its isservice flag is false and its currency and default price list use the validated NOK setup

#### Scenario: Product NOK setup is unavailable
- **WHEN** NOK currency or price-list validation fails
- **THEN** no Product mutation is attempted, local data and remote identity remain saved, and the failure is reported

### Requirement: Single-service visits supply a product-line duration
When a visit selects exactly one active product and that product is TJN, its new Resco Work Order product line SHALL receive estimatedduration and estimatedquantity in minutes equal to the visit's contract-line duration, because Resco displays service quantities as minutes. This value SHALL be captured in the durable application snapshot so retries use the same estimate. Actual duration/usage SHALL NOT be set. Product masters and template tasks SHALL NOT receive the visit-specific duration. Physical products and visits with multiple products SHALL NOT receive an invented duration allocation. Existing populated estimates and actual usage SHALL remain unchanged by ordinary rescheduling.

#### Scenario: Create a single-service visit
- **WHEN** a 45-minute visit with one TJN product is synced
- **THEN** its Work Order product line has estimatedduration 45 and estimatedquantity 45 and no actual duration is supplied

#### Scenario: Retry after a partial failure
- **WHEN** product-line creation is retried after the visit definition changes
- **THEN** the original snapshotted estimate and remembered line identity are reused

#### Scenario: Multiple or physical products
- **WHEN** a visit has multiple selected products or its sole product is PRD
- **THEN** no visit-duration estimate is allocated to those lines
