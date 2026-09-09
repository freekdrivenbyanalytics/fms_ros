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

# TomTom's Standard plan caps a single matrix at 2,500 cells (origins x
# destinations) and appears to cancel synchronous requests around a ~30s
# internal compute budget. Since our matrix is always square (origins ==
# destinations == the region's location set), cap the synchronous path well
# under that limit and fall back to the async submit/poll/download flow
# above it.
_SYNC_CELL_LIMIT = 900
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


def _request_matrix(endpoints: list[LocationEndpoint]) -> list[dict]:
    points = [{"point": {"latitude": e.latitude, "longitude": e.longitude}} for e in endpoints]
    body = {"origins": points, "destinations": points, "options": _MATRIX_OPTIONS}
    cell_count = len(points) * len(points)
    if cell_count <= _SYNC_CELL_LIMIT:
        return _request_matrix_sync(body)
    return _request_matrix_async(body)


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
