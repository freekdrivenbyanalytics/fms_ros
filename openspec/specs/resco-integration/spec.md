# resco-integration Specification

## Purpose

Keeps Resco (the field service mobile CRM technicians log into) aware of fms_ros's employees, by pushing each one to Resco as a User, so a technician added or updated in fms_ros doesn't need to be entered separately in Resco.

## Requirements

### Requirement: Employees are synced to Resco as Users
The system SHALL let employee data be pushed to Resco by creating or updating a corresponding User record in Resco, sending that employee's first name, last name, email, and mobile phone.

#### Scenario: A new employee is created as a User in Resco
- **WHEN** an employee with no remembered Resco User ID is synced
- **THEN** the system creates a new User in Resco with that employee's first name, last name, email, and mobile phone, and remembers the returned Resco User ID against that employee

#### Scenario: An existing employee's User in Resco is updated
- **WHEN** an employee with a remembered Resco User ID is synced
- **THEN** the system updates that Resco User's first name, last name, email, and mobile phone rather than creating a new one

### Requirement: An employee missing a field Resco requires is skipped, not failed
The system SHALL require an email and a mobile phone number to sync an employee to Resco. An employee missing either SHALL be skipped for that sync, reported as skipped, and SHALL NOT prevent other employees in the same sync from being processed.

#### Scenario: An employee missing email or mobile phone is skipped
- **WHEN** a sync processes an employee with no email, no mobile phone, or neither
- **THEN** the system does not call Resco for that employee, reports it as skipped, and continues processing the remaining employees

#### Scenario: One employee's Resco failure does not block others
- **WHEN** a sync processes multiple employees and Resco returns an error for one of them
- **THEN** the system reports that employee as failed and still attempts every other employee in the sync

### Requirement: Employees sync to Resco automatically on create and update
The system SHALL attempt to sync an employee to Resco immediately after that employee is created or updated. A failure of this automatic sync (Resco unreachable, an error response, or a missing required field) SHALL NOT fail or roll back the employee create or update itself.

#### Scenario: Creating an employee triggers a sync attempt
- **WHEN** a user creates an employee
- **THEN** the system attempts to sync that employee to Resco after the employee is persisted, and the employee is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating an employee triggers a sync attempt
- **WHEN** a user updates an employee
- **THEN** the system attempts to sync that employee to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

### Requirement: A user can manually trigger syncing all employees
The system SHALL let a user trigger a sync of every non-deleted employee to Resco on demand, returning a summary of how many were created, updated, skipped, and failed.

#### Scenario: Manually syncing all employees
- **WHEN** a user triggers a manual sync
- **THEN** the system attempts to sync every non-deleted employee to Resco and returns a summary counting how many were created, updated, skipped (missing required fields), and failed (a Resco error)

### Requirement: Customers are synced to Resco as Accounts
The system SHALL let customer data be pushed to Resco by creating or updating a corresponding Account record in Resco, sending that customer's name, email, phone, organization/VAT number, and address. Each portal customer SHALL map to one Account, named after the customer, regardless of its number of locations. Contact-person name and mobile SHALL also be synced when present, with exact Resco mappings verified before implementation. Changes and explicit clears SHALL update that same Account using Customer.resco_account_id. Customer updates SHALL NOT replace location-specific functional-location addresses or coordinates.

#### Scenario: A new customer is created as an Account in Resco
- **WHEN** a customer with no remembered Resco Account ID is synced
- **THEN** the system creates a new Account in Resco with that customer's name, email, phone, organization number, and address, and remembers the returned Resco Account ID against that customer

#### Scenario: An existing customer's Account in Resco is updated
- **WHEN** a customer with a remembered Resco Account ID is synced
- **THEN** the system updates that Resco Account's name, email, phone, organization number, and address rather than creating a new one

### Requirement: Customer locations are synced to Resco as Assets
The system SHALL let customer location data be pushed to Resco by creating or updating a corresponding Asset record in Resco, using exactly the same name as its Resco functional location and linking it to both that functional location and its parent customer's Resco Account. The functional location SHALL be synced first; each portal location SHALL have its own Asset, reused on subsequent syncs. Both names SHALL use the portal location's address, the existing location display name.

#### Scenario: A new customer location is created as an Asset in Resco
- **WHEN** a customer location with no remembered Resco Asset ID is synced, and its customer has a remembered Resco Account ID
- **THEN** the system creates a new Asset in Resco with the same name as the location's functional location, linked to that functional location and the customer's Resco Account, and remembers the returned Resco Asset ID against that location

#### Scenario: An existing customer location's Asset in Resco is updated
- **WHEN** a customer location with a remembered Resco Asset ID is synced
- **THEN** the system updates that Asset's name and links using its remembered ID, keeping its name equal to the functional location name rather than creating a new one

#### Scenario: A customer location whose customer isn't yet synced is skipped
- **WHEN** a customer location is synced and its customer has no remembered Resco Account ID
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations — it becomes eligible again once its customer is synced

#### Scenario: A customer location with no street address is skipped
- **WHEN** a customer location with no street address is synced
- **THEN** the system does not call Resco for that location, reports it as skipped, and continues processing the remaining locations

### Requirement: Customers and customer locations sync to Resco automatically on create and update
The system SHALL attempt to sync a customer to Resco immediately after that customer is created or updated, and a customer location to Resco immediately after that location is created or updated. A failure of this automatic sync (Resco unreachable, an error response, or a missing required dependency) SHALL NOT fail or roll back the customer or customer-location create or update itself.

#### Scenario: Creating a customer triggers a Resco sync attempt
- **WHEN** a user creates a customer
- **THEN** the system attempts to sync that customer to Resco after it is persisted, and the customer is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a customer triggers a Resco sync attempt
- **WHEN** a user updates a customer
- **THEN** the system attempts to sync that customer to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

#### Scenario: Creating a customer location triggers a Resco sync attempt
- **WHEN** a user creates a customer location
- **THEN** the system attempts to sync that location to Resco after it is persisted, and the location is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a customer location triggers a Resco sync attempt
- **WHEN** a user updates a customer location
- **THEN** the system attempts to sync that location to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

### Requirement: A user can manually trigger syncing all customers or all customer locations to Resco
The system SHALL let a user trigger a sync of every non-deleted customer to Resco on demand, and separately a sync of every non-deleted customer location to Resco on demand, each returning a summary of how many were created, updated, skipped, and failed.

#### Scenario: Manually syncing all customers
- **WHEN** a user triggers a manual customer sync to Resco
- **THEN** the system attempts to sync every non-deleted customer to Resco and returns a summary counting how many were created, updated, and failed

#### Scenario: Manually syncing all customer locations
- **WHEN** a user triggers a manual customer location sync to Resco
- **THEN** the system attempts to sync every non-deleted customer location to Resco and returns a summary counting how many were created, updated, skipped (customer not yet synced, or the location has no street address), and failed

### Requirement: Products are synced to Resco
The system SHALL let product data be pushed to Resco by creating or updating a corresponding Product record in Resco, sending that product's name and product number.

#### Scenario: A new product is created in Resco
- **WHEN** a product with no remembered Resco Product ID is synced
- **THEN** the system creates a new Product in Resco with that product's name and number, and remembers the returned Resco Product ID against that product

#### Scenario: An existing product's Resco record is updated
- **WHEN** a product with a remembered Resco Product ID is synced
- **THEN** the system updates that Resco Product's name and number rather than creating a new one

### Requirement: Products sync to Resco on create and update
The system SHALL attempt to sync a product to Resco immediately after that product is created or updated in fms_ros. A failure of this automatic sync SHALL NOT fail or roll back the product create or update itself.

#### Scenario: Creating a product triggers a sync attempt
- **WHEN** a user creates a product in fms_ros
- **THEN** the system attempts to sync that product to Resco after it is persisted, and the product is persisted regardless of whether that sync attempt succeeds

#### Scenario: Updating a product triggers a sync attempt
- **WHEN** a user updates a product in fms_ros
- **THEN** the system attempts to sync that product to Resco after the update is persisted, and the update is persisted regardless of whether that sync attempt succeeds

### Requirement: Assignments are synced to Resco as Work Orders
The system SHALL let assignment data be pushed to Resco by creating or updating a corresponding Work Order record in Resco, sending that assignment's planned start and end time, the assigned employee (as the Work Order's resource, via that employee's remembered Resco User ID), the visit's customer location (as the Work Order's linked asset, via that location's remembered Resco Asset ID), and the visit's parent customer (as the Work Order's required customer reference, via Customer.resco_account_id). The Work Order's name SHALL identify both the customer and the customer location ("Customer name: address | Visit <service_visit_id>"), so different locations and repeated visits are distinguishable. The visit suffix SHALL be retained within the 160-character name limit; names SHALL NOT be used as identity keys. A newly created Work Order SHALL end up in a scheduled state in Resco, not left in an incomplete/draft state, once its required fields and schedule are both present.

#### Scenario: A new assignment is created as a Work Order in Resco
- **WHEN** an assignment with no remembered Resco Work Order ID is synced
- **THEN** the system creates a new Work Order in Resco with that assignment's planned start and end time, resource, linked asset, and customer, and remembers the returned Resco Work Order ID against that assignment

#### Scenario: A reassigned assignment's Work Order in Resco is updated
- **WHEN** an assignment with a remembered Resco Work Order ID is synced after its employee or planned time has changed
- **THEN** the system updates that Resco Work Order's resource and/or planned start and end time rather than creating a new one

#### Scenario: A newly synced Work Order is scheduled, not draft
- **WHEN** an assignment is synced to Resco for the first time, creating its Work Order and schedule
- **THEN** the resulting Work Order does not remain in an incomplete/draft state in Resco - it has every field Resco requires to be considered scheduled

### Requirement: An assignment whose employee or location isn't yet synced to Resco is skipped, not failed
The system SHALL require the assignment's employee to have a remembered Resco User ID and the visit's customer location to have both a remembered Resco functional location ID and a remembered Resco Asset ID, with its parent customer having a remembered Resco Account ID to sync an assignment to Resco. An assignment missing either SHALL be skipped for that sync, reported as skipped, and SHALL NOT prevent the assignment itself from being created, or other assignments in the same batch from being synced.

#### Scenario: An assignment whose employee isn't yet synced to Resco is skipped
- **WHEN** an assignment is synced whose employee has no remembered Resco User ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and the assignment is still created

#### Scenario: An assignment whose customer location isn't yet synced to Resco is skipped
- **WHEN** an assignment is synced whose visit's customer location lacks its functional location or Asset ID, or its parent customer lacks an Account ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and the assignment is still created

#### Scenario: One assignment's Resco failure does not block others in the same apply
- **WHEN** applying a proposed schedule creates or updates multiple assignments and Resco returns an error for one of them
- **THEN** the system reports that assignment's sync as failed and still attempts every other assignment's sync in the same apply

### Requirement: Assignments sync to Resco automatically when scheduled or rescheduled
The system SHALL attempt to sync an assignment to Resco immediately after it is created or has its employee or planned time changed, whether that happens through manually assigning a visit or through applying a proposed schedule. A failure of this automatic sync (Resco unreachable, an error response, or a missing required dependency) SHALL NOT fail or roll back the assignment create or update itself.

#### Scenario: Manually assigning a visit triggers a sync attempt
- **WHEN** a user manually assigns a visit to an employee
- **THEN** the system attempts to sync that assignment to Resco after it is persisted, and the assignment is persisted regardless of whether that sync attempt succeeds

#### Scenario: Applying a proposed schedule triggers a sync attempt per assignment
- **WHEN** a user applies a proposed schedule
- **THEN** the system attempts to sync each assignment it creates or reassigns to Resco, and the apply's own result is unaffected by whether any of those sync attempts succeed



### Requirement: An assignment's Resco Work Order status can be pulled on demand
The system SHALL let a user trigger, on demand only (no automatic or scheduled job), a bulk pull of the current Resco Work Order status for every assignment with a remembered Resco Work Order ID, storing each one's latest status locally. An assignment with no remembered Resco Work Order ID SHALL be skipped, reported as skipped, and SHALL NOT prevent the pull from continuing to the remaining assignments. A failure pulling one assignment's status SHALL NOT prevent the pull from continuing to the remaining assignments.

#### Scenario: Pulling status updates the locally stored value
- **WHEN** a user triggers a status pull and an assignment has a remembered Resco Work Order ID
- **THEN** the system fetches that Work Order's current status from Resco and stores it against the assignment, replacing whatever was previously stored

#### Scenario: An assignment never synced to Resco is skipped
- **WHEN** a user triggers a status pull and an assignment has no remembered Resco Work Order ID
- **THEN** the system does not call Resco for that assignment, reports it as skipped, and continues with the remaining assignments

#### Scenario: One assignment's pull failure does not block the rest
- **WHEN** a status pull processes multiple assignments and fetching one fails
- **THEN** the system continues pulling status for the remaining assignments and reports the failure for that one

#### Scenario: The status pull only runs on demand
- **WHEN** the backend starts, or at any other automatic trigger point
- **THEN** no Resco Work Order status pull runs automatically; it only runs when a user explicitly triggers it

### Requirement: Eligible overdue reconciliation resets the Work Order to Draft
The system SHALL attempt to reset the existing Work Order to Draft (statecode 0, statuscode 1) when portal reconciliation unassigns a past planned assignment whose previously synced Work Order is currently Scheduled. It SHALL NOT reset other statuses or reset Work Orders on ordinary manual unassignment. A failed reset SHALL NOT roll back local unassignment; the system SHALL report the failure and preserve the remote identity and reset context for retry independently of the deleted assignment. A retry SHALL recheck eligibility and SHALL NOT overwrite subsequent field progress.

#### Scenario: Eligible work is returned to Draft
- **WHEN** reconciliation unassigns an eligible past Scheduled assignment
- **THEN** the portal attempts to set that same Work Order to Draft without deleting it

#### Scenario: Remote reset fails
- **WHEN** Resco rejects or cannot receive the Draft reset
- **THEN** the visit remains unassigned locally, the failure is reported, and reset context remains available for retry

#### Scenario: Ordinary manual unassignment leaves Resco untouched
- **WHEN** a user manually unassigns a visit outside overdue reconciliation
- **THEN** this change does not trigger a remote status reset

### Requirement: Customer locations are synced to Resco as functional locations
The system SHALL create or update one Resco functional location per portal customer-location, named using the location's address (its existing portal display name), sending its address fields and optional latitude/longitude. It SHALL remember the returned technical ID on CustomerLocation.resco_functional_location_id and reuse it for updates. Each functional location SHALL have one portal-managed Asset with exactly the same name, linked through resco_functionallocationid_resco_functionallocation and to the parent customer Account through customerid_account. A location SHALL NOT create its own Resco Account. Equal names SHALL NOT merge distinct portal locations; remembered technical IDs determine identity.

#### Scenario: A customer has two locations
- **WHEN** one customer with two locations is synced
- **THEN** Resco has one customer Account, two functional locations with their respective addresses and coordinates, and one same-named Asset under each functional location, both Assets linked to that Account

#### Scenario: Coordinates are missing or added later
- **WHEN** a location without coordinates is synced and later receives coordinates
- **THEN** its functional location and Asset can be created without coordinates and the next sync updates the same functional location with the resolved coordinates

#### Scenario: An existing location changes
- **WHEN** a location address or coordinates change
- **THEN** sync updates the existing functional location and keeps its Asset name equal to the functional location name without changing other locations

#### Scenario: Functional location creation succeeds but Asset creation fails
- **WHEN** the functional location is created but the subsequent Asset operation fails
- **THEN** its technical ID remains saved for retry and the retry creates no duplicate functional location

#### Scenario: Existing Assets acquire functional locations
- **WHEN** a portal location already has a remembered Asset but no functional location ID
- **THEN** sync creates and remembers its functional location, updates the existing Asset's name and functional-location link, and retains the parent customer Account

### Requirement: Work Orders use the Asset of the visit's functional location
The system SHALL bind an assigned visit's Work Order to the Asset remembered on that visit's portal customer-location, which SHALL link to that same location's Resco functional location. The Work Order's customer SHALL be the parent customer's Resco Account. It SHALL NOT choose an arbitrary Asset belonging to the customer or create a location-specific Account. Missing dependencies SHALL skip the remote Work Order sync with an explanation without failing the local assignment.

#### Scenario: Visits at different locations of one customer
- **WHEN** two assigned visits for different locations of the same customer are synced
- **THEN** both Work Orders reference the same Account and each references the Asset belonging to its own functional location

### Requirement: Customer contact updates remain shared across locations
The system SHALL update the parent customer's single Resco Account with name, organization number, contact-person name, email, telephone and mobile, including explicit clears. It SHALL reuse existing portal fields and add missing editing support. Resco Account or linked Contact field mappings SHALL be verified before implementation. Every location's Asset SHALL remain linked to this Account so customer contact masterdata is shared rather than copied into location Accounts. Remote failures SHALL be reported and retryable without rolling back the local customer write.

#### Scenario: Contact information changes for a customer with multiple locations
- **WHEN** a customer contact value changes or is cleared
- **THEN** sync updates the same parent Account, all location Assets retain that Account link, and each functional location keeps its own address and coordinates

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
