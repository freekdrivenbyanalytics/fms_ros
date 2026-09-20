# Spec Delta

## MODIFIED Requirements

### Requirement: Resetting demo data removes local records that mirror the deleted Tripletex data
The system SHALL, as part of a confirmed reset, permanently remove (not soft-delete) every locally persisted service visit, assignment, contract, contract line, customer, and customer location, so reseeding starts from a clean local slate.

#### Scenario: Locally persisted visit and contract data is permanently removed
- **WHEN** a confirmed reset runs
- **THEN** every service visit, assignment, contract, and contract line previously persisted locally is permanently removed, not merely marked deleted

#### Scenario: Locally persisted customers and customer locations are permanently removed
- **WHEN** a confirmed reset runs
- **THEN** every customer and customer location previously persisted locally is permanently removed, not merely marked deleted

#### Scenario: Employees are not removed
- **WHEN** a confirmed reset runs
- **THEN** existing employees remain persisted, unaffected by the reset

### Requirement: Reseeding creates contracts and contract lines from bundled demo data
The system SHALL, after locally creating customers and customer locations, create a contract and a contract line for each entry in the bundled demo contract-line data, linking each contract line to its corresponding locally created customer location and to one product chosen for it from the bundled data, and generate that contract line's unassigned service visits using the same generation rule applied when a contract line is created through the API.

#### Scenario: Bundled contract lines are created and linked
- **WHEN** the local-seeding step runs after local customer and customer-location creation
- **THEN** the system creates one contract line per entry in the bundled demo contract-line data, each linked to the customer location and product the bundled data specifies for it

#### Scenario: Seeded contract lines generate their service visits
- **WHEN** a bundled contract line is created during reseeding
- **THEN** the system generates its unassigned service visits the same way it would for a contract line created through the ordinary contract-line API

## REMOVED Requirements

### Requirement: Reseeding creates fresh customers and customer locations in Tripletex from bundled demo data
**Reason**: fms_ros is now the system of record - the reseed step creates customers and customer locations locally first (fms_ros-assigned ids, immediately usable, no Tripletex round-trip needed before local seeding continues), not directly in Tripletex.
**Migration**: See the new "Reseeding creates fresh customers and customer locations locally from bundled demo data" requirement.

### Requirement: Reseeding syncs the newly created Tripletex data locally
**Reason**: this described pulling Tripletex's just-created customer/location records into the local database, and locally assigning each `CustomerLocation` the same id as its Tripletex delivery address - both premises no longer hold: fms_ros no longer pulls from Tripletex at all, and a `CustomerLocation`'s id is fms_ros-assigned, never Tripletex's.
**Migration**: See "Reseeding creates fresh customers and customer locations locally from bundled demo data" (local creation now comes first, with an fms_ros-assigned id immediately, no sync required before local seeding continues) and the new "Reseeding pushes the newly created local data to Tripletex" requirement (the push now happens after local seeding, not before).

## ADDED Requirements

### Requirement: Reseeding creates fresh customers and customer locations locally from bundled demo data
The system SHALL, after the reset, create locally (with fms_ros-assigned ids, no Tripletex id yet) a customer and a customer location for each entry in the bundled demo customer data.

#### Scenario: Bundled customers are created locally
- **WHEN** the reseed step runs after a reset
- **THEN** the system creates, locally, one customer and one customer location for each entry in the bundled demo customer data, each with an fms_ros-assigned id

### Requirement: Reseeding pushes the newly created local data to Tripletex
The system SHALL, after local customer, customer-location, contract, contract-line, and service-visit seeding is complete, push every newly created customer and customer location to Tripletex, using the same bootstrap-sync behavior available on demand elsewhere in the system, so the connected Tripletex account ends up populated with the demo scenario too.

#### Scenario: Newly seeded local data is pushed to Tripletex after seeding
- **WHEN** local seeding has finished creating customers, customer locations, contracts, contract lines, and service visits
- **THEN** the system pushes every newly created customer and customer location to Tripletex, creating a corresponding record for each and remembering its Tripletex id
