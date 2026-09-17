# admin-portal Specification

## Purpose

Gives a planner a dedicated, standalone area for internal masterdata management that doesn't belong in the customer-facing portal, kept clearly separate from Planning, the Customer Portal, and Employee Management. This iteration moves region management here, with full CRUD and a map for defining each region's geographic extent.

## Requirements

### Requirement: Admin Portal is a separate top-level area
The system SHALL provide the Admin Portal as a top-level area reachable via a landing entry point distinct from the Planning application's navigation, the Customer Portal, and Employee Management, sharing no header or navigation elements with any of them.

#### Scenario: User reaches the Admin Portal
- **WHEN** a user navigates to the Admin Portal's entry point
- **THEN** the system shows the Admin Portal without any Planning-application, Customer Portal, or Employee Management navigation visible alongside it

#### Scenario: Admin Portal and Planning share the same data
- **WHEN** the same backend/database that serves the Planning application also serves the Admin Portal
- **THEN** any region, product, contract, or customer location visible in the Planning application is also visible in the Admin Portal, and vice versa

### Requirement: Region list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted regions and a detail view for each region showing its own fields (name, geo-shape), the employees scoped to it, and the customer locations located in it.

#### Scenario: User browses the region list
- **WHEN** a user opens the region list view in the Admin Portal
- **THEN** the system shows every non-deleted region currently in the database

#### Scenario: User opens a region's detail view
- **WHEN** a user opens a region's detail view in the Admin Portal
- **THEN** the system shows that region's own fields, the employees scoped to it, and the customer locations located in it

### Requirement: Create, update, and soft-delete a region from the Admin Portal
The system SHALL let a user create a region with a name, update its name, and soft-delete it, from the Admin Portal.

#### Scenario: Creating a region in the Admin Portal
- **WHEN** a user creates a region from the Admin Portal
- **THEN** the system persists the new region and it appears in the region list

#### Scenario: Updating a region's name in the Admin Portal
- **WHEN** a user updates a region's name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a region in the Admin Portal
- **WHEN** a user soft-deletes a region from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the region list

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

### Requirement: Compute driving times for a region from the Admin Portal
The system SHALL let a user, from the Admin Portal's Regions view, trigger driving-time computation for a region, alongside the existing "re-assign regions" action. While computation is in progress the system SHALL indicate that it is running, and SHALL show a result or error message once it completes.

#### Scenario: Triggering driving-time computation
- **WHEN** a user clicks the "Compute driving times" action in the Admin Portal's Regions view for a region
- **THEN** the system triggers that region's driving-time computation and, once it completes, shows a result message

#### Scenario: Computation in progress is indicated
- **WHEN** a user triggers driving-time computation and it has not yet completed
- **THEN** the system shows that computation is in progress and disables re-triggering it until it finishes

#### Scenario: A failed computation is reported
- **WHEN** driving-time computation for a region fails
- **THEN** the system shows an error message rather than silently discarding the failure

### Requirement: Product list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted products and a detail view for each product showing its own fields, its required skills and service order type, and the contract lines that require it. The system SHALL NOT provide any control on this view to change which contract lines are associated with a product — that association remains editable only from the Admin Portal's own Contracts view.

#### Scenario: User browses the product list
- **WHEN** a user opens the product list view in the Admin Portal
- **THEN** the system shows every non-deleted product currently in the database

#### Scenario: User opens a product's detail view
- **WHEN** a user opens a product's detail view in the Admin Portal
- **THEN** the system shows that product's own fields, its required skills and service order type, and the contract lines that require it, without any control to add or remove a contract line association

### Requirement: Create, update, and soft-delete a product from the Admin Portal
The system SHALL let a user create a product with a product type, a number, and a name, update a product's type, number, or name, and soft-delete a product, from the Admin Portal's Products view.

#### Scenario: Creating a product in the Admin Portal
- **WHEN** a user creates a product from the Admin Portal
- **THEN** the system persists the new product and it appears in the Products list

#### Scenario: Updating a product in the Admin Portal
- **WHEN** a user updates a product's type, number, or name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a product in the Admin Portal
- **WHEN** a user soft-deletes a product from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Products list

### Requirement: Refresh products from Tripletex
The system SHALL provide a control on the Admin Portal's Products view that triggers an on-demand Tripletex product sync, and SHALL refresh the Products view's data after the sync completes.

#### Scenario: Planner refreshes products
- **WHEN** a user activates the Refresh control on the Products view
- **THEN** the system triggers a Tripletex product sync, and once it completes, the Products view reflects the resulting data

### Requirement: Skills view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted skills and a detail view for each showing its own fields and the products that require it.

#### Scenario: User browses the skills list
- **WHEN** a user opens the skills list view in the Admin Portal
- **THEN** the system shows every non-deleted skill currently in the database

#### Scenario: User opens a skill's detail view
- **WHEN** a user opens a skill's detail view in the Admin Portal
- **THEN** the system shows that skill's own fields and the products that require it

### Requirement: Create, update, and soft-delete a skill from the Admin Portal
The system SHALL let a user create a skill with a name, update its name, and soft-delete it, from the Admin Portal's Skills view.

#### Scenario: Creating a skill in the Admin Portal
- **WHEN** a user creates a skill from the Admin Portal
- **THEN** the system persists the new skill and it appears in the Skills list

#### Scenario: Updating a skill in the Admin Portal
- **WHEN** a user updates a skill's name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a skill in the Admin Portal
- **WHEN** a user soft-deletes a skill from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Skills list

### Requirement: Service Order Types view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted service order types and a detail view for each showing its own fields and the products assigned it.

#### Scenario: User browses the service order types list
- **WHEN** a user opens the service order types list view in the Admin Portal
- **THEN** the system shows every non-deleted service order type currently in the database

#### Scenario: User opens a service order type's detail view
- **WHEN** a user opens a service order type's detail view in the Admin Portal
- **THEN** the system shows that service order type's own fields and the products assigned it

### Requirement: Create, update, and soft-delete a service order type from the Admin Portal
The system SHALL let a user create a service order type with a name, update its name, and soft-delete it, from the Admin Portal's Service Order Types view.

#### Scenario: Creating a service order type in the Admin Portal
- **WHEN** a user creates a service order type from the Admin Portal
- **THEN** the system persists the new service order type and it appears in the Service Order Types list

#### Scenario: Updating a service order type in the Admin Portal
- **WHEN** a user updates a service order type's name from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a service order type in the Admin Portal
- **WHEN** a user soft-deletes a service order type from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Service Order Types list

### Requirement: Product detail view shows and edits required skills and service order type
The system SHALL let a user, from the Admin Portal's Products view, see and edit which skills a product requires and which service order type it has.

#### Scenario: Viewing a product's skills and service order type
- **WHEN** a user opens a product's detail view in the Admin Portal
- **THEN** the system shows the skills it requires and its service order type, if any

#### Scenario: Editing a product's skills and service order type
- **WHEN** a user updates which skills a product requires or which service order type it has, from the Admin Portal
- **THEN** the system persists the change

### Requirement: Contract list and detail views
The system SHALL provide, within the Admin Portal, a list view of all non-deleted contracts and a detail view for each contract showing its own fields, the customer it belongs to, and its contract lines, each showing its customer location, dates, interval, duration, and required products.

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
The system SHALL let a user create a contract line under a contract — for one of that contract's customer's locations — update its customer location, dates, interval, duration, and required products, and soft-delete it, from the Admin Portal's Contract detail view.

#### Scenario: Creating a contract line in the Admin Portal
- **WHEN** a user creates a contract line under a contract from the Admin Portal, selecting one of that contract's customer's locations
- **THEN** the system persists the new contract line and it appears under that contract

#### Scenario: Updating a contract line in the Admin Portal
- **WHEN** a user updates a contract line's customer location, dates, interval, duration, or required products from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a contract line in the Admin Portal
- **WHEN** a user soft-deletes a contract line from the Admin Portal
- **THEN** the system marks it deleted, it no longer appears under its contract, and any service visits already generated from it (and any assignment made against one of those visits) are permanently removed

### Requirement: Mark a contract line as open-ended from the Admin Portal
The system SHALL let a user, on the Admin Portal's contract-line form, check a "No end date" box to indicate the line has no end date. Checking it SHALL grey out and disable the end-date field and display `31.12.2099` in it as a placeholder; unchecking it SHALL re-enable the field for a real date. The form SHALL submit `end_date: null` whenever the box is checked, regardless of what is displayed in the disabled field.

#### Scenario: Marking a line as open-ended
- **WHEN** a user checks the "No end date" box on the contract-line form
- **THEN** the end-date field becomes disabled, shows `31.12.2099`, and the form submits `end_date: null` on save

#### Scenario: Unmarking an open-ended line
- **WHEN** a user unchecks the "No end date" box
- **THEN** the end-date field becomes editable again and the form submits whatever real date the user enters

#### Scenario: An existing open-ended line shows the box checked
- **WHEN** a user opens the edit form for a contract line that has no end_date
- **THEN** the "No end date" box is shown checked and the end-date field shows `31.12.2099`, disabled

### Requirement: Contract line rows show their generated service visits
The system SHALL show, for each contract line displayed in the Admin Portal's Contracts view, the service visits generated from it, including each visit's requested date and status.

#### Scenario: Viewing a contract line's generated visits
- **WHEN** a user views a contract line in the Admin Portal's Contracts view
- **THEN** the system shows the service visits generated from that contract line, each with its requested date and status (unassigned or assigned)

#### Scenario: A contract line with no visits yet
- **WHEN** a user views a contract line that has no service visits
- **THEN** the system shows that it has no visits, rather than an error or a blank section

### Requirement: Extend recurring visits from the Admin Portal
The system SHALL let a user, from the Admin Portal's Contracts view, trigger the extend-visits operation for every open-ended contract line at once. While the operation is in progress the system SHALL indicate that it is running, and SHALL show a result or error message once it completes.

#### Scenario: Triggering extend-visits
- **WHEN** a user clicks the "Extend recurring visits" action in the Admin Portal's Contracts view
- **THEN** the system triggers the extend-visits operation and, once it completes, shows a result message

#### Scenario: Extension in progress is indicated
- **WHEN** a user triggers extend-visits and it has not yet completed
- **THEN** the system shows that it is in progress and disables re-triggering it until it finishes

#### Scenario: A failed extension is reported
- **WHEN** the extend-visits operation fails
- **THEN** the system shows an error message rather than silently discarding the failure

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

### Requirement: Create, update, and soft-delete a customer location from the Admin Portal
The system SHALL let a user create a customer location for an existing customer with an address, update a customer location's address, and soft-delete a customer location, from the Admin Portal's Customer Locations view. This is in addition to, and does not replace, the existing coordinate-override control on this view.

#### Scenario: Creating a customer location in the Admin Portal
- **WHEN** a user creates a customer location for a customer from the Admin Portal
- **THEN** the system persists the new customer location and it appears in the Customer Locations list

#### Scenario: Updating a customer location's address in the Admin Portal
- **WHEN** a user updates a customer location's address from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a customer location in the Admin Portal
- **WHEN** a user soft-deletes a customer location from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Customer Locations list

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

### Requirement: Customers view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted customers and a detail view for each showing its Tripletex-sourced fields (name, email, phone, organization number) and its Resco sync status.

#### Scenario: User browses the customer list
- **WHEN** a user opens the customer list view in the Admin Portal
- **THEN** the system shows every non-deleted customer currently in the database

#### Scenario: User opens a customer's detail view
- **WHEN** a user opens a customer's detail view in the Admin Portal
- **THEN** the system shows that customer's Tripletex-sourced fields and whether it has been synced to Resco

### Requirement: Create, update, and soft-delete a customer from the Admin Portal
The system SHALL let a user create a customer with a name, update a customer's fields, and soft-delete a customer, from the Admin Portal's Customers view.

#### Scenario: Creating a customer in the Admin Portal
- **WHEN** a user creates a customer from the Admin Portal
- **THEN** the system persists the new customer and it appears in the Customers list

#### Scenario: Updating a customer in the Admin Portal
- **WHEN** a user updates a customer's fields from the Admin Portal
- **THEN** the system persists the change

#### Scenario: Soft-deleting a customer in the Admin Portal
- **WHEN** a user soft-deletes a customer from the Admin Portal
- **THEN** the system marks it deleted and it no longer appears in the Customers list

### Requirement: Sync customers and customer locations to Resco from the Admin Portal
The system SHALL provide a control on the Admin Portal's Customers view that triggers an on-demand Resco customer sync, and a control on the Customer Locations view that triggers an on-demand Resco customer location sync, each showing the returned summary (created/updated/skipped/failed counts).

#### Scenario: Planner syncs customers to Resco
- **WHEN** a user activates the "Sync to Resco" control on the Customers view
- **THEN** the system triggers a Resco customer sync and shows the resulting summary

#### Scenario: Planner syncs customer locations to Resco
- **WHEN** a user activates the "Sync to Resco" control on the Customer Locations view
- **THEN** the system triggers a Resco customer location sync and shows the resulting summary
