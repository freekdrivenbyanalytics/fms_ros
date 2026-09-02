from sqlalchemy.orm import Session

from app.models import CustomerLocation, Region


def _point_in_polygon(lat: float, lng: float, polygon: list[dict]) -> bool:
    """Standard ray-casting point-in-polygon test over a geo_shape-shaped
    list of {"lat": ..., "lng": ...} points, treated as a simple polygon."""
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        lat_i, lng_i = polygon[i]["lat"], polygon[i]["lng"]
        lat_j, lng_j = polygon[j]["lat"], polygon[j]["lng"]
        if ((lng_i > lng) != (lng_j > lng)) and (
            lat < (lat_j - lat_i) * (lng - lng_i) / (lng_j - lng_i) + lat_i
        ):
            inside = not inside
        j = i
    return inside


def assign_regions_by_geofence(db: Session) -> None:
    """Assign each non-deleted customer location's region from its
    coordinates against each non-deleted region's geo_shape. A location with
    resolved coordinates matching exactly one region's shape (first match if
    more than one) gets that region; any other location (no match, or no
    resolved coordinates) has its region cleared."""
    regions = (
        db.query(Region)
        .filter(Region.delete_flag.is_(False), Region.geo_shape.isnot(None))
        .order_by(Region.id)
        .all()
    )
    locations = db.query(CustomerLocation).filter(CustomerLocation.delete_flag.is_(False)).all()

    for location in locations:
        matched_region_id = None
        if location.latitude is not None and location.longitude is not None:
            for region in regions:
                if _point_in_polygon(location.latitude, location.longitude, region.geo_shape):
                    matched_region_id = region.id
                    break
        location.region_id = matched_region_id
