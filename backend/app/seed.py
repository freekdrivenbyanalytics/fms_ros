from datetime import date, time, timedelta

from app.database import SessionLocal
from app.models import (
    Contract,
    Customer,
    CustomerLocation,
    Employee,
    Region,
    ServiceVisit,
    Skill,
)
from app.tripletex import sync_customers


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

        # Migrating to Tripletex-sourced customers truncates customer_locations
        # (and its dependents) but leaves regions/skills/employees untouched,
        # so an already-migrated dev database can have employees without
        # having customer locations. Guard on customer_locations specifically,
        # and get-or-create regions/skills/employees so re-running this after
        # migrating doesn't duplicate them.
        if db.query(CustomerLocation).count():
            print("Seed fixtures already present, skipping (customers synced).")
            return

        customers = db.query(Customer).order_by(Customer.id).limit(3).all()
        if len(customers) < 3:
            raise RuntimeError(
                "Expected at least 3 customers from Tripletex to seed demo "
                f"fixtures, got {len(customers)}."
            )
        customer_a, customer_b, customer_c = customers

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

        customer_a_location = CustomerLocation(
            customer=customer_a,
            region=north_holland,
            address="Prinsengracht 12, Amsterdam",
            latitude=52.3738,
            longitude=4.8910,
        )
        customer_b_location = CustomerLocation(
            customer=customer_b,
            region=utrecht,
            address="Neude 5, Utrecht",
            latitude=52.0925,
            longitude=5.1197,
        )
        customer_c_hq = CustomerLocation(
            customer=customer_c,
            region=south_holland,
            address="Coolsingel 40, Rotterdam",
            latitude=51.9233,
            longitude=4.4792,
        )
        customer_c_branch = CustomerLocation(
            customer=customer_c,
            region=south_holland,
            address="Blaak 10, Rotterdam",
            latitude=51.9214,
            longitude=4.4886,
        )
        locations = [
            customer_a_location,
            customer_b_location,
            customer_c_hq,
            customer_c_branch,
        ]
        db.add_all(locations)
        db.flush()

        contracts = [
            Contract(
                customer_location=customer_a_location,
                start_date=date(2026, 8, 20),
                interval_days=30,
                duration_minutes=60,
                required_skills=[general_maintenance],
            ),
            Contract(
                customer_location=customer_b_location,
                start_date=date(2026, 8, 20),
                interval_days=14,
                duration_minutes=90,
                required_skills=[plumbing],
            ),
            Contract(
                customer_location=customer_c_hq,
                start_date=date(2026, 8, 21),
                interval_days=7,
                duration_minutes=45,
                required_skills=[electrical],
            ),
            Contract(
                customer_location=customer_c_branch,
                start_date=date(2026, 8, 22),
                interval_days=21,
                duration_minutes=30,
                required_skills=[hvac, general_maintenance],
            ),
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
            f"Synced customers from Tripletex; seeded {len(regions)} regions, "
            f"{len(skills)} skills, {len(locations)} customer locations, "
            f"{len(contracts)} contracts, {len(employees)} employees, "
            f"and {len(visits)} service visits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
