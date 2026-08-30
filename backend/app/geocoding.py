from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

_geolocator = Nominatim(user_agent="fms_ros")
_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1)


def geocode_address(address: str) -> tuple[float, float] | None:
    """Resolve an address to (latitude, longitude), or None if unresolved.

    Rate-limited to Nominatim's 1-request/second usage policy.
    """
    location = _geocode(address)
    if location is None:
        return None
    return location.latitude, location.longitude
