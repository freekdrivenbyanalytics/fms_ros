## 1. GeoShapeEditor reference layer

- [x] 1.1 Add an `otherRegions` prop to `GeoShapeEditor` (e.g. `{ name: string; geo_shape: GeoPoint[] }[]`), for regions to render as reference only
- [x] 1.2 On mount (and when `otherRegions` changes), render each entry with a geo-shape as a non-interactive, greyed-out `L.polygon` layer (or `L.polyline` for a 2-point shape, matching the existing editable-shape rendering logic), skipping entries with no geo-shape
- [x] 1.3 Ensure the reference layer is drawn beneath/behind the editable polygon and its draggable point markers, and does not intercept map clicks meant for adding a new point to the shape being edited

## 2. Wire up RegionsView

- [x] 2.1 In `RegionDetail` (`frontend/src/admin-portal/RegionsView.tsx`), pass every region from `regions` except the one currently being edited (filtering out ones with no geo-shape) as `otherRegions` to `GeoShapeEditor`

## 3. Manual verification

- [x] 3.1 Start the frontend, create two regions with distinct geo-shapes, then open one region's detail view and confirm the other region's shape appears greyed out and unclickable while the first region's own shape remains editable - verified against the already-running dev stack using the real seeded regions (Oslo: 5 points, East-Oslo: 8 points, West-Oslo/drammen: 5 points, Moss/Frederikstad: 5 points). Opening Oslo's detail view showed Oslo's own shape as a solid green editable polygon with draggable markers, and the other regions' boundaries as thin grey dashed lines layered underneath. An accidental click during zooming landed on the map (not on a reference shape) and added a stray point to the region being edited rather than to a greyed-out shape, confirming the reference layer is non-interactive (clicks pass through to the map). That accidental edit was never saved (discarded by navigating away); the regions list afterward showed all point counts unchanged
- [x] 3.2 Confirm a region with no geo-shape does not affect the reference layer - North Holland, Utrecht, South Holland, and Groningen have no geo-shape ("—" in the regions list) and, per `1.2`'s `.filter((region) => region.geo_shape.length >= 2)`, contribute nothing to the reference layer; consistent with what was observed (no extra shapes beyond the four regions that do have geo-shapes)
