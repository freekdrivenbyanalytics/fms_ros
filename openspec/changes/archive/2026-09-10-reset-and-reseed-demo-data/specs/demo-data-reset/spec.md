## Purpose

Lets the team reset the Tripletex-connected demo environment and the local database to a larger, more realistic customer scenario in one repeatable run, so scheduling, routing, and the Admin Portal can be stress-tested against data that resembles a real customer base rather than a handful of hand-written fixtures.

## ADDED Requirements

### Requirement: Resetting demo data requires explicit confirmation
The system SHALL provide a script that resets and reseeds the demo environment, and SHALL refuse to perform any destructive action unless it is explicitly invoked with a confirmation flag.

#### Scenario: Running without confirmation does nothing destructive
- **WHEN** the reset script is run without the confirmation flag
- **THEN** the system performs no deletion, in Tripletex or locally, and reports that confirmation is required

#### Scenario: Running with confirmation proceeds
- **WHEN** the reset script is run with the confirmation flag
- **THEN** the system proceeds with the reset and reseed sequence

### Requirement: Resetting demo data deletes existing Tripletex customers and customer locations
The system SHALL, as part of a confirmed reset, attempt to delete every customer in the connected Tripletex account via the Tripletex API (each customer's delivery address is cascaded away with it — Tripletex has no standalone delivery-address delete endpoint). A customer the API refuses to delete (e.g. one with pre-existing ledger/invoice history) SHALL be logged and skipped rather than aborting the reset. Products SHALL NOT be deleted or otherwise modified in Tripletex.

#### Scenario: All deletable Tripletex customers and their locations are removed
- **WHEN** a confirmed reset runs
- **THEN** every customer previously present in the connected Tripletex account that the API allows to be deleted is deleted from Tripletex, along with its customer location, and any customer the API refuses to delete is reported

#### Scenario: Tripletex products are left untouched
- **WHEN** a confirmed reset runs
- **THEN** no product in the connected Tripletex account is deleted or modified

### Requirement: Resetting demo data removes local records that mirror the deleted Tripletex data
The system SHALL, as part of a confirmed reset, permanently remove (not soft-delete) every locally persisted service visit, assignment, contract, contract line, customer, and customer location, since the Tripletex records they were synced from no longer exist.

#### Scenario: Locally persisted visit and contract data is permanently removed
- **WHEN** a confirmed reset runs
- **THEN** every service visit, assignment, contract, and contract line previously persisted locally is permanently removed, not merely marked deleted

#### Scenario: Locally persisted customers and customer locations are permanently removed
- **WHEN** a confirmed reset runs
- **THEN** every customer and customer location previously persisted locally is permanently removed, not merely marked deleted

#### Scenario: Employees are not removed
- **WHEN** a confirmed reset runs
- **THEN** existing employees remain persisted, unaffected by the reset

### Requirement: Reseeding creates fresh customers and customer locations in Tripletex from bundled demo data
The system SHALL, after the reset, create in Tripletex a customer and a customer location (delivery address) for each entry in the bundled demo customer data, via the Tripletex API.

#### Scenario: Bundled customers are created in Tripletex
- **WHEN** the reseed step runs after a reset
- **THEN** the system creates, in Tripletex, one customer and one customer location for each entry in the bundled demo customer data

### Requirement: Reseeding syncs the newly created Tripletex data locally
The system SHALL, after creating customers and customer locations in Tripletex, run the existing Tripletex-to-local customer and customer-location sync so the newly created records are reflected in the local database before local seeding continues.

#### Scenario: Newly created Tripletex data appears locally before local seeding
- **WHEN** the reseed step has finished creating customers and customer locations in Tripletex
- **THEN** the system runs the existing customer and customer-location sync, and every newly created Tripletex customer and customer location is persisted locally before contracts are seeded

### Requirement: Reseeding creates contracts and contract lines from bundled demo data
The system SHALL, after syncing, create a contract and a contract line for each entry in the bundled demo contract-line data, linking each contract line to its corresponding synced customer location and to one product chosen for it from the bundled data, and generate that contract line's unassigned service visits using the same generation rule applied when a contract line is created through the API.

#### Scenario: Bundled contract lines are created and linked
- **WHEN** the local-seeding step runs after a sync
- **THEN** the system creates one contract line per entry in the bundled demo contract-line data, each linked to the customer location and product the bundled data specifies for it

#### Scenario: Seeded contract lines generate their service visits
- **WHEN** a bundled contract line is created during reseeding
- **THEN** the system generates its unassigned service visits the same way it would for a contract line created through the ordinary contract-line API

### Requirement: Reseeding updates existing employees' product portfolios
The system SHALL, as part of reseeding, assign every existing employee all of the demo scenario's products, except for one designated employee, who SHALL be assigned every demo product except one specific product held back for that employee.

#### Scenario: Most employees receive the full demo product set
- **WHEN** reseeding updates employee products
- **THEN** every existing employee except the one designated employee has every demo product in their portfolio

#### Scenario: The designated employee is missing one product
- **WHEN** reseeding updates employee products
- **THEN** the designated employee has every demo product except the one held back for them

### Requirement: Bundled demo customer data represents a realistic Oslo/Akershus spread
The bundled demo customer data SHALL contain approximately 150 customer entries, most of them located in Oslo, with the remainder located in Akershus, each with a real geocodable address and resolved coordinates.

#### Scenario: Demo customers are concentrated in Oslo with some in Akershus
- **WHEN** the bundled demo customer data is inspected
- **THEN** most entries have an Oslo address and the rest have an Akershus address, and every entry's address resolves to real coordinates

### Requirement: Bundled demo contract-line data gives each customer a twice-monthly visit cadence
Each entry in the bundled demo contract-line data SHALL specify a 15-day interval and no end date, and SHALL specify exactly one of the demo scenario's products chosen independently at random for that entry.

#### Scenario: Each seeded contract line repeats every 15 days indefinitely
- **WHEN** a bundled contract line is created during reseeding
- **THEN** its interval is 15 days and it has no end date

#### Scenario: Each seeded contract line requires exactly one product
- **WHEN** a bundled contract line is created during reseeding
- **THEN** it requires exactly one of the demo scenario's products
