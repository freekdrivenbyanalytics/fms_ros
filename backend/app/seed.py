import random
from datetime import date, time, timedelta

from app.database import SessionLocal
from app.models import (
    Contract,
    CustomerLocation,
    Employee,
    Region,
    ServiceVisit,
    Skill,
)
from app.tripletex import sync_customer_locations, sync_customers


def _get_or_create(db, model, name: str, **extra):
    instance = db.query(model).filter_by(name=name).first()
    if instance is None:
        instance = model(name=name, **extra)
        db.add(instance)
        db.flush()
    return instance


def seed() -> None:
    db = SessionLocal()
    try:
        sync_customers(db)
        sync_customer_locations(db)

        north_holland = _get_or_create(db, Region, "North Holland")
        utrecht = _get_or_create(db, Region, "Utrecht")
        south_holland = _get_or_create(db, Region, "South Holland")
        groningen = _get_or_create(db, Region, "Groningen")
        regions = [north_holland, utrecht, south_holland, groningen]

        plumbing = _get_or_create(db, Skill, "Plumbing")
        electrical = _get_or_create(db, Skill, "Electrical")
        hvac = _get_or_create(db, Skill, "HVAC")
        general_maintenance = _get_or_create(db, Skill, "General Maintenance")
        skills = [plumbing, electrical, hvac, general_maintenance]

        employees = []
        if not db.query(Employee).count():
            employees = [
                Employee(
                    name="Alice Johnson",
                    work_start=time(8, 0),
                    work_end=time(16, 0),
                    latitude=52.3676,
                    longitude=4.9041,
                    regions=[north_holland, utrecht],
                    skills=[electrical, general_maintenance],
                ),
                Employee(
                    name="Bram de Vries",
                    work_start=time(9, 0),
                    work_end=time(17, 0),
                    latitude=52.0907,
                    longitude=5.1214,
                    regions=[utrecht],
                    skills=[plumbing],
                ),
                Employee(
                    name="Chen Wei",
                    work_start=time(7, 30),
                    work_end=time(15, 30),
                    latitude=51.9244,
                    longitude=4.4777,
                    regions=[south_holland, groningen],
                    skills=[hvac, general_maintenance],
                ),
            ]
            db.add_all(employees)

        # Tripletex is the source of truth for locations themselves; region
        # assignment is local and deferred (see sync_customer_locations), so
        # the demo needs to fill it in itself. Reuse this file's original
        # per-location region choices for as many locations as they cover,
        # and a random existing region for any location beyond that list —
        # Tripletex may return a different number of locations than this
        # fixture list was written for.
        locations = (
            db.query(CustomerLocation)
            .filter(CustomerLocation.delete_flag.is_(False))
            .order_by(CustomerLocation.id)
            .all()
        )
        default_regions_by_position = [north_holland, utrecht, south_holland, south_holland]
        for index, location in enumerate(locations):
            if location.region_id is not None:
                continue
            if index < len(default_regions_by_position):
                location.region = default_regions_by_position[index]
            else:
                location.region = random.choice(regions)

        if db.query(Contract).count():
            db.commit()
            print("Contract/visit fixtures already present, skipping (customers/locations synced).")
            return

        contract_fixtures = [
            {
                "start_date": date(2026, 8, 20),
                "interval_days": 30,
                "duration_minutes": 60,
                "required_skills": [general_maintenance],
            },
            {
                "start_date": date(2026, 8, 20),
                "interval_days": 14,
                "duration_minutes": 90,
                "required_skills": [plumbing],
            },
            {
                "start_date": date(2026, 8, 21),
                "interval_days": 7,
                "duration_minutes": 45,
                "required_skills": [electrical],
            },
            {
                "start_date": date(2026, 8, 22),
                "interval_days": 21,
                "duration_minutes": 30,
                "required_skills": [hvac, general_maintenance],
            },
        ]

        contracts = [
            Contract(
                customer_location=location,
                start_date=fixture["start_date"],
                interval_days=fixture["interval_days"],
                duration_minutes=fixture["duration_minutes"],
                required_skills=fixture["required_skills"],
            )
            for location, fixture in zip(locations, contract_fixtures)
        ]
        db.add_all(contracts)
        db.flush()

        visits = []
        for contract in contracts:
            for occurrence in range(2):
                visits.append(
                    ServiceVisit(
                        contract=contract,
                        requested_date=contract.start_date
                        + timedelta(days=occurrence * contract.interval_days),
                    )
                )
        db.add_all(visits)

        db.commit()
        print(
            f"Synced customers/locations from Tripletex; seeded {len(regions)} regions, "
            f"{len(skills)} skills, {len(locations)} customer locations, "
            f"{len(contracts)} contracts, {len(employees)} employees, "
            f"and {len(visits)} service visits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
