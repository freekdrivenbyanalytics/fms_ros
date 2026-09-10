"""Geocode CustomerLocation rows that are missing coordinates (e.g. because
Nominatim was rate-limiting or unreachable when they were created), without
touching Tripletex or recreating any data.

A plain re-sync (sync_customer_locations) won't retry these: it only
re-geocodes when a location's address has changed, and these locations'
addresses haven't. This targets exactly the rows still missing coordinates.

Usage: python -m app.backfill_location_coordinates
"""
from app.database import SessionLocal
from app.geocoding import geocode_address
from app.models import CustomerLocation


def backfill_location_coordinates() -> None:
    db = SessionLocal()
    try:
        locations = (
            db.query(CustomerLocation)
            .filter(
                CustomerLocation.latitude.is_(None),
                CustomerLocation.coordinates_locked.is_(False),
            )
            .all()
        )
        resolved = 0
        resolved_by_fallback = 0
        failed = 0
        for location in locations:
            coords = geocode_address(location.address)
            if coords is None and location.postal_code and location.city:
                # Some street names aren't indexed by Nominatim for their
                # city even though the address is real; falling back to
                # postal-code + city still gives a real, reasonably-placed
                # point instead of leaving the location uncoordinated.
                coords = geocode_address(f"{location.postal_code} {location.city}, Norge")
                if coords is not None:
                    resolved_by_fallback += 1
            if coords is None:
                failed += 1
                continue
            location.latitude, location.longitude = coords
            resolved += 1
            db.commit()

        print(
            f"Geocoded {resolved}/{len(locations)} location(s) "
            f"({resolved_by_fallback} via postal-code/city fallback); "
            f"{failed} still unresolved."
        )
    finally:
        db.close()


if __name__ == "__main__":
    backfill_location_coordinates()
