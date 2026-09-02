## MODIFIED Requirements

### Requirement: Admin Portal is a separate top-level area
The system SHALL provide the Admin Portal as a top-level area reachable via a landing entry point distinct from the Planning application's navigation, the Customer Portal, and Employee Management, sharing no header or navigation elements with any of them.

#### Scenario: User reaches the Admin Portal
- **WHEN** a user navigates to the Admin Portal's entry point
- **THEN** the system shows the Admin Portal without any Planning-application, Customer Portal, or Employee Management navigation visible alongside it

#### Scenario: Admin Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Admin Portal
- **THEN** any region, skill, contract, or customer location visible in the Planning application is also visible in the Admin Portal, and vice versa

### Requirement: Draw and adjust a region's geo-shape on a map
The system SHALL let a user, from a region's detail view in the Admin Portal, draw a new geo-shape by placing coordinate points on a map, or adjust an existing geo-shape by moving, adding, or removing its points, and save the result. The map SHALL also show every customer location with resolved coordinates as a marker, so a user can see which locations fall inside or outside the shape being drawn.

#### Scenario: Drawing a geo-shape for a region with none
- **WHEN** a user draws a polygon by placing three or more points on the map for a region that has no geo-shape
- **THEN** the system persists that polygon as the region's geo-shape

#### Scenario: Adjusting an existing geo-shape
- **WHEN** a user moves, adds, or removes points of a region's existing geo-shape on the map and saves
- **THEN** the system persists the updated polygon in place of the previous one

#### Scenario: A region without a geo-shape shows an empty map
- **WHEN** a user opens the map for a region that has no geo-shape yet
- **THEN** the map shows no polygon, ready for the user to start drawing one

#### Scenario: Customer locations are shown on the map
- **WHEN** a user opens the map for any region
- **THEN** the system shows every customer location that has resolved coordinates as a marker on the map, distinguishable from the shape's own point markers

### Requirement: Region cross-references are read-only in the Admin Portal
The system SHALL NOT provide any control on a region's own detail view in the Admin Portal to change which employees or customer locations are associated with it; those associations remain editable only from Employee Management (employees) or the Regions view's "re-assign regions" action (customer locations).

#### Scenario: No employee-assignment control on the region detail view
- **WHEN** a user views a region's detail view in the Admin Portal
- **THEN** the system shows the employees scoped to that region without any control to add or remove one

#### Scenario: No customer-location-assignment control on the region detail view
- **WHEN** a user views a region's detail view in the Admin Portal
- **THEN** the system shows the customer locations in that region without any control to add or remove one

### Requirement: Skill cross-references are read-only in the Admin Portal
The system SHALL NOT provide any control in the Admin Portal to change which employees or contract lines are associated with a skill; those associations remain editable only from Employee Management (employees) or the Admin Portal's own Contracts view (contract lines).

#### Scenario: No employee-assignment control on the skill detail view
- **WHEN** a user views a skill's detail view in the Admin Portal
- **THEN** the system shows the employees who hold that skill without any control to add or remove one

#### Scenario: No contract-line-assignment control on the skill detail view
- **WHEN** a user views a skill's detail view in the Admin Portal
- **THEN** the system shows the contract lines that require that skill without any control to add or remove one

## ADDED Requirements

### Requirement: Contract list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted contracts and a detail view for each contract showing its own fields, the customer it belongs to, and its contract lines, each showing its customer location, dates, interval, duration, and required skills.

#### Scenario: User browses the contract list
- **WHEN** a user opens the contract list view in the Admin Portal
- **THEN** the system shows every non-deleted contract currently in the database

#### Scenario: User opens a contract's detail view
- **WHEN** a user opens a contract's detail view in the Admin Portal
- **THEN** the system shows that contract's own fields, the customer it belongs to, and its contract lines

### Requirement: Create, update, and soft-delete a contract from the Admin Portal
The system SHALL let a user create a contract for a customer, update which customer it belongs to, and soft-delete it, from the Admin Portal's Contracts view.

#### Scenario: Creating a contract in the Admin Portal
- **WHEN** a user creates a contract for a customer from the Admin Portal
- **THEN** the system persists the new contract and it appears in the Contracts list

#### Scenario: Updating a contract in the Admin Portal
- **WHEN** a user updates a contract's customer from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract in the Admin Portal
- **WHEN** a user soft-deletes a contract from the Admin Portal
- **THEN** the system marks it deleted, it no longer appears in the Contracts list, and its contract lines are also marked deleted with their generated service visits permanently removed

### Requirement: Create, update, and soft-delete a contract line from the Admin Portal
The system SHALL let a user create a contract line under a contract — for one of that contract's customer's locations — update its customer location, dates, interval, duration, and required skills, and soft-delete it, from the Admin Portal's Contract detail view.

#### Scenario: Creating a contract line in the Admin Portal
- **WHEN** a user creates a contract line under a contract from the Admin Portal, selecting one of that contract's customer's locations
- **THEN** the system persists the new contract line and it appears under that contract

#### Scenario: Updating a contract line in the Admin Portal
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required skills from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract line in the Admin Portal
- **WHEN** a user soft-deletes a contract line from the Admin Portal
- **THEN** the system marks it deleted, it no longer appears under its contract, and any service visits already generated from it (and any assignment made against one of those visits) are permanently removed

### Requirement: Contract line rows show their generated service visits
The system SHALL show, for each contract line displayed in the Admin Portal's Contracts view, the service visits generated from it, including each visit's requested date and status.

#### Scenario: Viewing a contract line's generated visits
- **WHEN** a user views a contract line in the Admin Portal's Contracts view
- **THEN** the system shows the service visits generated from that contract line, each with its requested date and status (unassigned or assigned)

#### Scenario: A contract line with no visits yet
- **WHEN** a user views a contract line that has no service visits
- **THEN** the system shows that it has no visits, rather than an error or a blank section

### Requirement: Customer Locations view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted customer locations and a detail view for each showing its own fields, the customer it belongs to, the region it is in, and whether its coordinates are locked against sync overwrites.

#### Scenario: User browses the customer location list
- **WHEN** a user opens the customer location list view in the Admin Portal
- **THEN** the system shows every non-deleted customer location currently in the database

#### Scenario: User opens a customer location's detail view
- **WHEN** a user opens a customer location's detail view in the Admin Portal
- **THEN** the system shows that location's own fields, the customer it belongs to, the region it is in, and whether its coordinates are locked

### Requirement: Override a customer location's coordinates from the Admin Portal
The system SHALL let a user set or correct a customer location's latitude and longitude from its detail view in the Admin Portal, and check a box that marks the location's coordinates as locked, preventing a future Tripletex sync's geocoding step from overwriting them.

#### Scenario: Setting coordinates manually
- **WHEN** a user enters a latitude and longitude for a customer location and saves
- **THEN** the system persists those coordinates for that location

#### Scenario: Locking coordinates against a future sync
- **WHEN** a user checks the "don't overwrite on refresh" box while setting a customer location's coordinates
- **THEN** the system persists the location as coordinates-locked, and a later sync's geocoding step does not change its latitude or longitude

#### Scenario: Unlocking coordinates
- **WHEN** a user unchecks the "don't overwrite on refresh" box for a previously locked customer location
- **THEN** the system persists it as no longer locked, and a later sync's geocoding step may update its coordinates again

### Requirement: Customer location region is read-only in the Admin Portal's Customer Locations view
The system SHALL NOT provide any control on a customer location's own detail view in the Admin Portal to directly set or change its region; a location's region is derived from its coordinates only when a user triggers the Regions view's "re-assign regions" action.

#### Scenario: No region-assignment control on the customer location detail view
- **WHEN** a user views a customer location's detail view in the Admin Portal
- **THEN** the system shows its region without any control to set or change it directly

### Requirement: Re-assign customer locations to regions from the Admin Portal
The system SHALL let a user, from the Admin Portal's Regions view, trigger re-assignment of every customer location's region on demand: for each customer location, if its coordinates are resolved and exactly one non-deleted region's geo-shape contains that point, the system SHALL set that customer location's region to it; otherwise — coordinates matching no region's geo-shape, or no resolved coordinates at all — the system SHALL clear that customer location's region. This action is manual and on demand — it does not run automatically as part of any Tripletex sync, so a region's geo-shape can be drawn or adjusted and immediately followed by re-assigning locations, without needing a Tripletex refresh first.

#### Scenario: Triggering region re-assignment
- **WHEN** a user clicks the "re-assign regions" action in the Admin Portal's Regions view
- **THEN** the system re-evaluates every customer location against every region's current geo-shape, setting each location's region where exactly one match is found and clearing it otherwise

#### Scenario: A location's coordinates fall within no region's geo-shape
- **WHEN** a user triggers region re-assignment and a customer location's coordinates fall within no region's geo-shape
- **THEN** the system clears that customer location's region, even if it previously had one

#### Scenario: A location with no coordinates has its region cleared
- **WHEN** a user triggers region re-assignment and a customer location has no resolved coordinates
- **THEN** the system clears that customer location's region, even if it previously had one

#### Scenario: Adjusting a geo-shape and re-running picks up new matches
- **WHEN** a user adjusts a region's geo-shape and then triggers region re-assignment again
- **THEN** customer locations newly inside that shape are assigned to it, and locations no longer inside any shape have their region cleared

#### Scenario: Region re-assignment does not happen automatically on sync
- **WHEN** a Tripletex sync runs, whether at startup or via the refresh control
- **THEN** no customer location's region is changed as a result
