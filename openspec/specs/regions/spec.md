# regions Specification

## Purpose

Represents named geographic regions used to group employees and customer locations for regional visibility on the assignment page.

## Requirements

### Requirement: Region data model
The system SHALL persist each region with a unique identifier, a name, an optional geo-shape describing its geographic extent, and a soft-delete flag. A region's geo-shape is an ordered list of two or more latitude/longitude coordinate pairs forming a polygon. A region with no geo-shape SHALL remain otherwise usable.

#### Scenario: Region is persisted with required fields
- **WHEN** a region record is created with id and name
- **THEN** the system persists the region and both fields are retrievable unchanged, with no geo-shape unless one was given

#### Scenario: Region is persisted with a geo-shape
- **WHEN** a region is created or updated with a geo-shape of three or more coordinate pairs
- **THEN** the system persists the geo-shape and it is retrievable unchanged

#### Scenario: An existing region without a geo-shape remains usable
- **WHEN** a region has no geo-shape
- **THEN** the region is still retrievable and usable everywhere a region is referenced (employee regions, customer location region)

### Requirement: Create, update, and soft-delete a region
The system SHALL allow a user to create a region with a name and an optional geo-shape, update its name and geo-shape, and soft-delete it. A soft-deleted region SHALL NOT be permanently removed.

#### Scenario: Creating a region
- **WHEN** a user creates a region with a name
- **THEN** the system persists a new region with that name and no geo-shape

#### Scenario: Adding a geo-shape to an existing region
- **WHEN** a user updates an existing region to add a geo-shape
- **THEN** the system persists the geo-shape for that region

#### Scenario: Adjusting a region's geo-shape
- **WHEN** a user updates a region's existing geo-shape with a different set of coordinate pairs
- **THEN** the system persists the new geo-shape in place of the old one

#### Scenario: Soft-deleting a region
- **WHEN** a user soft-deletes a region
- **THEN** the system marks it deleted rather than removing it, and it no longer appears in the default region list, while any employees or customer locations still referencing it remain unaffected

### Requirement: Deleted regions are hidden by default
The system SHALL exclude regions marked deleted from the region list returned to callers by default.

#### Scenario: Deleted region is excluded from the list
- **WHEN** a caller requests the list of regions
- **THEN** regions marked deleted are not included in the result

### Requirement: Region editor shows other regions for reference
While a user is creating or editing a region's geo-shape, the system SHALL display every other existing region's geo-shape on the same map as a greyed-out, non-interactive reference layer, distinct in appearance from the region currently being edited.

#### Scenario: Other regions appear greyed out while editing
- **WHEN** a user opens the geo-shape editor for a region
- **THEN** every other existing region that has a geo-shape is drawn on the map in a greyed-out style, and the region being edited is drawn in its normal editable style

#### Scenario: Greyed-out regions are not interactive
- **WHEN** a user clicks or drags on a greyed-out region shown for reference
- **THEN** the click or drag has no effect on the region currently being edited or on the greyed-out region

#### Scenario: A region with no geo-shape contributes nothing to the reference layer
- **WHEN** another existing region has no geo-shape
- **THEN** the system draws nothing for that region in the reference layer
