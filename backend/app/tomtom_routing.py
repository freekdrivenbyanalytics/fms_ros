from __future__ import annotations

import time as time_module
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import CustomerLocation, DrivingTime, Employee, LocationKind, Region

MATRIX_BASE_URL = "https://api.tomtom.com/routing/matrix/2"

# "departAt": "any" + "traffic": "historical" returns a static, typical travel
# time derived from historical speed data rather than live/real-time traffic,
# per design.md's decision to not condition driving times on time of day.
# routeType/travelMode are pinned explicitly since TomTom's 400km x 400km
# origin/destination bounding-box restriction (Standard plan) is lifted only
# when departAt/arriveAt="any", traffic="historical", routeType="fastest",
# and travelMode is "car" or "truck".
_MATRIX_OPTIONS = {
    "departAt": "any",
    "traffic": "historical",
    "routeType": "fastest",
    "travelMode": "car",
}

# TomTom's Standard plan caps the async endpoint at 2,500 cells (origins x
# destinations) total per request - confirmed against the live API, which
# rejects an oversized job with a BAD_ARGUMENT "matrix size and parameters
# combination violates the API limitations" error rather than processing it.
# A region with more than 50 endpoints can't be covered by one request at
# all, so its full N x N matrix is tiled into BLOCK_SIZE x BLOCK_SIZE request
# chunks (see _request_matrix) that are each requested and merged locally.
_MAX_CELLS_PER_REQUEST = 2500
_BLOCK_SIZE = int(_MAX_CELLS_PER_REQUEST**0.5)

# The synchronous endpoint has its own, much lower cap - 200 cells on a
# Standard plan even with the unlimited-bounding-box option combo below
# (confirmed against the live API: a 500-cell rectangular sync request was
# rejected with the same BAD_ARGUMENT error). Chunks at or under this size
# use the synchronous endpoint; larger ones use the async submit/poll/
# download flow, up to _MAX_CELLS_PER_REQUEST.
_SYNC_CELL_LIMIT = 200
_POLL_INTERVAL_SECONDS = 2.0
_POLL_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class LocationEndpoint:
    kind: LocationKind
    id: int
    latitude: float
    longitude: float


def build_region_location_set(db: Session, region: Region) -> list[LocationEndpoint]:
    """A region's driving-time location endpoints: its non-deleted customer
    locations with resolved coordinates, plus the home location of every
    non-deleted employee scoped to it."""
    locations = (
        db.query(CustomerLocation)
        .filter(
            CustomerLocation.region_id == region.id,
            CustomerLocation.delete_flag.is_(False),
            CustomerLocation.latitude.isnot(None),
            CustomerLocation.longitude.isnot(None),
        )
        .all()
    )
    employees = (
        db.query(Employee)
        .filter(Employee.delete_flag.is_(False))
        .options(joinedload(Employee.regions))
        .all()
    )
    region_employees = [e for e in employees if any(r.id == region.id for r in e.regions)]

    endpoints = [
        LocationEndpoint(LocationKind.CUSTOMER_LOCATION, loc.id, loc.latitude, loc.longitude)
        for loc in locations
    ]
    endpoints += [
        LocationEndpoint(LocationKind.EMPLOYEE, emp.id, emp.latitude, emp.longitude)
        for emp in region_employees
    ]
    return endpoints


def _request_matrix_sync(body: dict) -> list[dict]:
    response = httpx.post(
        MATRIX_BASE_URL,
        params={"key": settings.tomtom_api_key},
        json=body,
        timeout=httpx.Timeout(35.0),
    )
    response.raise_for_status()
    return response.json()["data"]


def _request_matrix_async(body: dict) -> list[dict]:
    submit_response = httpx.post(
        f"{MATRIX_BASE_URL}/async",
        params={"key": settings.tomtom_api_key},
        json=body,
        timeout=httpx.Timeout(35.0),
    )
    submit_response.raise_for_status()
    job_id = submit_response.json()["jobId"]

    deadline = time_module.monotonic() + _POLL_TIMEOUT_SECONDS
    while True:
        status_response = httpx.get(
            f"{MATRIX_BASE_URL}/async/{job_id}",
            params={"key": settings.tomtom_api_key},
            timeout=httpx.Timeout(10.0),
        )
        status_response.raise_for_status()
        state = status_response.json()["state"]
        if state == "Completed":
            break
        if state == "Failed":
            raise RuntimeError(f"TomTom matrix job {job_id} failed")
        if time_module.monotonic() > deadline:
            raise TimeoutError(f"TomTom matrix job {job_id} did not complete in time")
        time_module.sleep(_POLL_INTERVAL_SECONDS)

    result_response = httpx.get(
        f"{MATRIX_BASE_URL}/async/{job_id}/result",
        params={"key": settings.tomtom_api_key},
        headers={"Accept-Encoding": "gzip"},
        timeout=httpx.Timeout(35.0),
    )
    result_response.raise_for_status()
    return result_response.json()["data"]


def _to_points(endpoints: list[LocationEndpoint]) -> list[dict]:
    return [{"point": {"latitude": e.latitude, "longitude": e.longitude}} for e in endpoints]


def _request_matrix_block(
    origins: list[LocationEndpoint],
    destinations: list[LocationEndpoint],
    origin_offset: int,
    destination_offset: int,
) -> list[dict]:
    """Request one origins x destinations block and remap its cells'
    originIndex/destinationIndex (which TomTom returns relative to this
    block's own point lists) back to indices into the full endpoint list."""
    body = {
        "origins": _to_points(origins),
        "destinations": _to_points(destinations),
        "options": _MATRIX_OPTIONS,
    }
    cell_count = len(origins) * len(destinations)
    cells = _request_matrix_sync(body) if cell_count <= _SYNC_CELL_LIMIT else _request_matrix_async(body)
    for cell in cells:
        cell["originIndex"] += origin_offset
        cell["destinationIndex"] += destination_offset
    return cells


def _request_matrix(endpoints: list[LocationEndpoint]) -> list[dict]:
    """The full origins x destinations matrix for endpoints (both lists are
    the same region-wide set), tiled into <= _MAX_CELLS_PER_REQUEST chunks
    since that's TomTom's per-request cap regardless of sync vs async."""
    n = len(endpoints)
    if n * n <= _MAX_CELLS_PER_REQUEST:
        return _request_matrix_block(endpoints, endpoints, 0, 0)

    cells: list[dict] = []
    for origin_offset in range(0, n, _BLOCK_SIZE):
        origin_block = endpoints[origin_offset : origin_offset + _BLOCK_SIZE]
        for destination_offset in range(0, n, _BLOCK_SIZE):
            destination_block = endpoints[destination_offset : destination_offset + _BLOCK_SIZE]
            cells.extend(
                _request_matrix_block(origin_block, destination_block, origin_offset, destination_offset)
            )
    return cells


def compute_region_driving_times(db: Session, region: Region) -> dict:
    """Compute and persist a region's driving-time matrix from TomTom,
    replacing any previously stored entries for that region. Returns a
    summary of how many ordered pairs were computed vs. skipped (TomTom
    could not return a route for that pair)."""
    endpoints = build_region_location_set(db, region)
    if len(endpoints) < 2:
        db.query(DrivingTime).filter(DrivingTime.region_id == region.id).delete()
        db.commit()
        return {"computed": 0, "skipped": 0}

    cells = _request_matrix(endpoints)

    computed = 0
    skipped = 0
    new_rows = []
    for cell in cells:
        origin_index = cell["originIndex"]
        destination_index = cell["destinationIndex"]
        if origin_index == destination_index:
            continue
        route_summary = cell.get("routeSummary")
        if route_summary is None:
            skipped += 1
            continue
        origin = endpoints[origin_index]
        destination = endpoints[destination_index]
        new_rows.append(
            DrivingTime(
                region_id=region.id,
                origin_kind=origin.kind,
                origin_id=origin.id,
                destination_kind=destination.kind,
                destination_id=destination.id,
                duration_minutes=round(route_summary["travelTimeInSeconds"] / 60),
            )
        )
        computed += 1

    db.query(DrivingTime).filter(DrivingTime.region_id == region.id).delete()
    db.add_all(new_rows)
    db.commit()
    return {"computed": computed, "skipped": skipped}


ROUTE_BASE_URL = "https://api.tomtom.com/routing/1/calculateRoute"


@dataclass(frozen=True)
class RoutePoint:
    latitude: float
    longitude: float


def compute_employee_day_route(stops: list[LocationEndpoint]) -> list[RoutePoint] | None:
    """Calls TomTom's Calculate Route API with `stops` chained as ordered
    waypoints (e.g. an employee's home followed by that day's visits in
    planned order), returning the full road-following polyline - every leg's
    points concatenated in order - or None if TomTom could not find a route
    covering all of them.

    Unlike the driving-time matrix, this is never persisted: it's recomputed
    on every day-planning-map view (see design.md's "No result caching").
    """
    if len(stops) < 2:
        return []

    locations = ":".join(f"{stop.latitude},{stop.longitude}" for stop in stops)
    try:
        response = httpx.get(
            f"{ROUTE_BASE_URL}/{locations}/json",
            params={"key": settings.tomtom_api_key, "routeType": "fastest"},
            timeout=httpx.Timeout(35.0),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    routes = response.json().get("routes")
    if not routes:
        return None
    legs = routes[0].get("legs")
    if not legs:
        return None

    return [
        RoutePoint(latitude=point["latitude"], longitude=point["longitude"])
        for leg in legs
        for point in leg["points"]
    ]
