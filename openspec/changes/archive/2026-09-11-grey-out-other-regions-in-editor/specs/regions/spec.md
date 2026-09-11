## ADDED Requirements

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
