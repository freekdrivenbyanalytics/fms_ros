# Spec Delta

## MODIFIED Requirements

### Requirement: Assignment data model
The system SHALL persist each assignment with the service visit it applies to, the employee it is assigned to, a planned start time, a planned end time, and its last known Resco Work Order status once one has been pulled.

#### Scenario: Assignment is persisted with required fields
- **WHEN** an assignment is created linking a service visit to an employee with a planned start time
- **THEN** the system persists the assignment with the service_visit_id, employee_id, planned_start, and planned_end

#### Scenario: A new assignment has no Resco status until one is pulled
- **WHEN** an assignment is created
- **THEN** its Resco Work Order status is unset until a status pull (see the resco-integration capability) fetches one

### Requirement: An assignment locks automatically once it has started
The system SHALL treat an assignment as pinned — regardless of its stored pin flag — once its planned start time has passed. This lock is based on elapsed time, not the stored flag, and cannot be removed by unpinning. The one exception is the automatic unassignment of a past planned assignment whose synced Work Order is currently Scheduled (see "Past assignments whose Work Orders are currently Scheduled are automatically unassigned") — that reconciliation overrides this lock, since a past visit currently Scheduled has nothing left to protect from reassignment.

#### Scenario: An already-started assignment is shown as pinned
- **WHEN** a user views an assignment whose planned start time has already passed
- **THEN** the system shows that assignment as pinned, even if it was never manually pinned

#### Scenario: Unpinning an already-started assignment does not unlock it
- **WHEN** a user unpins an assignment whose planned start time has already passed
- **THEN** the system updates the stored pin flag, but the assignment continues to be shown as pinned and remains excluded from schedule runs

#### Scenario: The automatic overdue-unassignment reconciliation overrides the lock
- **WHEN** the past-Scheduled reconciliation processes an assignment that is locked (whether manually pinned or automatically locked by elapsed time)
- **THEN** the lock does not prevent that assignment from being automatically unassigned

### Requirement: View employees and visits for assignment
The system SHALL provide a page showing the list of employees, the list of unassigned service visits, and the list of assigned service visits, with each employee card showing its region(s) and products, and each visit card showing its customer name, region, and required products, all expandable to show additional detail. Each of the three lists SHALL provide its own independent text search and region/product filtering, narrowing that list without affecting the other two lists. Each assigned visit card SHALL show whether its assignment is pinned, its last known Resco Work Order status (if any has been pulled), and offer controls to unassign it and to pin or unpin it. An unassigned visit card whose visit was automatically unassigned by the overdue-reconciliation SHALL show that reason. The unassigned and assigned visit lists SHALL share a single date-range control: by default it includes every visit requested before today (no lower bound) through seven days from today; a "This Week" preset moves the upper bound to the end of the current calendar week, and a "4 Weeks" preset moves it to 28 days from today; in every case, visits requested before today remain included regardless of which upper bound is selected — except an assigned visit that is both requested before today and whose Resco Work Order status is completed, which is excluded from the assigned visit list regardless of the date range (it remains visible on the visit-history page).

#### Scenario: Planner views the assignment page
- **WHEN** a user opens the assignment page
- **THEN** the page displays all employees, all unassigned service visits, and all assigned service visits, each employee showing its region(s) and products, and each visit showing its customer name, region, and required products

#### Scenario: Planner expands a card for more detail
- **WHEN** a user clicks an employee or service visit card
- **THEN** the card expands to show an info box with additional detail not shown on the collapsed card (at least the region(s) for an employee; at least the address and GPS coordinates for a service visit, whether unassigned or assigned)

#### Scenario: Planner searches a list by name or address
- **WHEN** a user types text into a list's search box
- **THEN** that list shows only the employees or visits whose name (employee name, or visit's customer name) or, for a visit, location address, contains the search text, and the other two lists are unaffected

#### Scenario: Planner filters a list by region and skill
- **WHEN** a user selects one or more regions and/or one or more products in a list's filters
- **THEN** that list shows only the employees or visits that have at least one of the selected regions (if any region is selected) and at least one of the selected products (if any product is selected), and the other two lists are unaffected

#### Scenario: Search and filters combine within a list
- **WHEN** a user has both entered search text and selected region/product filters on the same list
- **THEN** that list shows only the employees or visits matching the search text and satisfying the selected filters

#### Scenario: No search text and no filters selected
- **WHEN** a list's search box is empty and no region or product filters are selected
- **THEN** that list shows every employee or visit it would show without search or filtering

#### Scenario: Assigned visit cards show pin state and actions
- **WHEN** a user views the assigned service visits list
- **THEN** each assigned visit card indicates whether it is pinned, and offers an "Unassign" action and a pin/unpin action

#### Scenario: Default date range shows overdue and near-term visits
- **WHEN** a user opens the assignment page without changing the date-range control
- **THEN** both the unassigned and assigned visit lists show only visits requested before today or within the next seven days

#### Scenario: "This Week" preset extends the range to the end of the current week
- **WHEN** a user selects the "This Week" preset
- **THEN** both visit lists show visits requested before today or up to the end of the current calendar week

#### Scenario: "4 Weeks" preset extends the range further out
- **WHEN** a user selects the "4 Weeks" preset
- **THEN** both visit lists show visits requested before today or up to 28 days from today

#### Scenario: Overdue visits are never hidden by the date range
- **WHEN** any date-range selection is active, whether the default or a preset, and an overdue assigned visit's Resco Work Order status is not completed (or not yet known)
- **THEN** that visit remains included in the assigned visit list regardless of the selected upper bound

#### Scenario: An overdue, completed assigned visit is hidden from the board
- **WHEN** an assigned visit's requested date is before today and its Resco Work Order status is completed
- **THEN** that visit is excluded from the assigned visit list, regardless of the selected date range

#### Scenario: Assigned visit cards show their Resco status
- **WHEN** a user views the assigned service visits list and an assignment has a last-known Resco Work Order status
- **THEN** that assignment's card shows that status

#### Scenario: An automatically-unassigned visit's card explains why
- **WHEN** a user views an unassigned service visit whose most recent assignment was removed by the overdue-reconciliation, not by a manual unassign
- **THEN** that visit's card shows that it was unassigned because its past planned Work Order is currently Scheduled

## ADDED Requirements

### Requirement: Past assignments whose Work Orders are currently Scheduled are automatically unassigned
As part of on-demand status sync, the system SHALL unassign an assignment only when its planned_start date is before today and a successful fresh read confirms its previously synced Work Order is currently Active/Scheduled (statecode 0, statuscode 5). It SHALL remove the local assignment, clear its pin, set the visit unassigned and record a reason. This narrow operation SHALL override pin/elapsed-time locks. It SHALL NOT use requested_date or assignment creation time to determine eligibility. It SHALL attempt the corresponding Draft reset specified by resco-integration. Unsynced assignments, failed reads and all other current statuses SHALL be left alone. Audit history and previously observed statuses SHALL NOT determine eligibility; a Work Order that returned to Scheduled is eligible based on its current status.

#### Scenario: An overdue, unsynced assignment is retained
- **WHEN** a past planned assignment has no remembered Work Order ID
- **THEN** reconciliation skips it and leaves it assigned

#### Scenario: A past assignment still Scheduled is unassigned
- **WHEN** the planned work date is before today and a successful read confirms the synced Work Order is currently Scheduled
- **THEN** reconciliation unassigns it locally with a reason, regardless of pin or elapsed-time lock, and attempts a Draft reset

#### Scenario: Another status preserves the assignment
- **WHEN** the Work Order is in any status other than Active/Scheduled
- **THEN** reconciliation leaves the assignment and remote status unchanged

#### Scenario: A failed status read preserves the assignment
- **WHEN** a current status cannot be read successfully
- **THEN** reconciliation reports the failure and does not act on an old cached Scheduled value

#### Scenario: A same-day or future assignment is never auto-unassigned
- **WHEN** planned_start falls today or later, even if requested_date is in the past
- **THEN** reconciliation does not unassign the visit

#### Scenario: The reason clears on reassignment
- **WHEN** an automatically unassigned visit is assigned again manually or through optimization
- **THEN** its unassigned_reason is cleared


#### Scenario: Audit history is unavailable
- **WHEN** a past planned Work Order is currently Scheduled and auditing is unavailable or its previous status was different
- **THEN** reconciliation uses the fresh current status and unassigns it without reading audit history
