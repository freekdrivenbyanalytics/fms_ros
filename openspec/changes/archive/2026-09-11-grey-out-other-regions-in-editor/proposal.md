## Why

When drawing or editing a region's geo-shape, a user can't see where other existing regions already are, making it easy to accidentally draw overlapping or misaligned boundaries.

## What Changes

- The region geo-shape editor (`GeoShapeEditor`) renders every other existing region's geo-shape as a greyed-out, non-interactive polygon on the same map, for visual reference while drawing or editing the current region's shape.
- Regions with no geo-shape have nothing to render and are unaffected.

## Capabilities

### Modified Capabilities
- `regions`: the region editor now shows other existing regions' geo-shapes, greyed out, while creating or editing a region's own geo-shape.

## Impact

- `frontend/src/shared/GeoShapeEditor.tsx`: accept a new prop for other regions' geo-shapes and render each as a non-interactive, greyed-out polygon layer, alongside the existing editable polygon and customer-location markers.
- `frontend/src/admin-portal/RegionsView.tsx`: pass every other region's geo-shape (all regions except the one being created/edited) into `GeoShapeEditor`.
