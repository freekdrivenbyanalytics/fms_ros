import random
from datetime import date, time, timedelta

from app.database import SessionLocal
from app.models import (
    Contract,
    ContractLine,
    CustomerLocation,
    DayType,
    Employee,
    EmployeeScheduleDayOverride,
    EmployeeScheduleTemplate,
    Product,
    Region,
    ServiceVisit,
)
from app.geofencing import assign_regions_by_geofence
from app.tripletex import sync_customer_locations, sync_customers, sync_products

# The only products seeded assignments are drawn from; kept deliberately
# small and specific rather than the full TJN catalog.
SEED_PRODUCT_NUMBERS = ["TJN10001", "TJN10018", "TJN10010"]


def _get_or_create(db, model, name: str, **extra):
    instance = db.query(model).filter_by(name=name).first()
    if instance is None:
        instance = model(name=name, **extra)
        db.add(instance)
        db.flush()
    return instance


def _random_products(products: list[Product]) -> list[Product]:
    """A random, non-empty (when possible) subset of the seed products."""
    if not products:
        return []
    return random.sample(products, random.randint(1, len(products)))


def seed() -> None:
    db = SessionLocal()
    try:
        sync_customers(db)
        sync_customer_locations(db)
        sync_products(db)
        assign_regions_by_geofence(db)

        north_holland = _get_or_create(db, Region, "North Holland")
        utrecht = _get_or_create(db, Region, "Utrecht")
        south_holland = _get_or_create(db, Region, "South Holland")
        groningen = _get_or_create(db, Region, "Groningen")
        regions = [north_holland, utrecht, south_holland, groningen]

        products = (
            db.query(Product).filter(Product.number.in_(SEED_PRODUCT_NUMBERS)).all()
        )

        employees = []
        if not db.query(Employee).count():
            employee_fixtures = [
                {
                    "first_name": "Alice",
                    "last_name": "Johnson",
                    "work_start": time(8, 0),
                    "work_end": time(16, 0),
                    "latitude": 52.3676,
                    "longitude": 4.9041,
                    "regions": [north_holland, utrecht],
                },
                {
                    "first_name": "Bram",
                    "last_name": "de Vries",
                    "work_start": time(9, 0),
                    "work_end": time(17, 0),
                    "latitude": 52.0907,
                    "longitude": 5.1214,
                    "regions": [utrecht],
                },
                {
                    "first_name": "Chen",
                    "last_name": "Wei",
                    "work_start": time(7, 30),
                    "work_end": time(15, 30),
                    "latitude": 51.9244,
                    "longitude": 4.4777,
                    "regions": [south_holland, groningen],
                },
            ]
            for fixture in employee_fixtures:
                employee = Employee(
                    first_name=fixture["first_name"],
                    last_name=fixture["last_name"],
                    latitude=fixture["latitude"],
                    longitude=fixture["longitude"],
                    regions=fixture["regions"],
                    products=_random_products(products),
                )
                db.add(employee)
                db.flush()
                employees.append(employee)

                template = EmployeeScheduleTemplate(
                    employee_id=employee.id,
                    start_date=date(2026, 1, 1),
                    end_date=None,
                    work_start=fixture["work_start"],
                    work_end=fixture["work_end"],
                    max_hours_per_day=8,
                )
                db.add(template)

            # Sample overrides on the first employee to exercise the
            # resolution logic: one holiday, one manually-adjusted working day.
            db.add(
                EmployeeScheduleDayOverride(
                    employee_id=employees[0].id,
                    date=date(2026, 9, 1),
                    day_type=DayType.HOLIDAY,
                )
            )
            db.add(
                EmployeeScheduleDayOverride(
                    employee_id=employees[0].id,
                    date=date(2026, 9, 2),
                    day_type=DayType.WORKING,
                    work_start=time(9, 0),
                    work_end=time(17, 0),
                )
            )

        # assign_regions_by_geofence above already placed every location whose
        # coordinates fall inside a region's geo-shape (and cleared the rest).
        # This is only a fallback for locations geofencing couldn't place (no
        # coordinates, or outside every shape): reuse this file's original
        # per-location region choices for as many as they cover, and a random
        # existing region for any location beyond that list — Tripletex may
        # return a different number of locations than this fixture list was
        # written for.
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

        contract_line_fixtures = [
            {
                "start_date": date(2026, 8, 20),
                "interval_days": 30,
                "duration_minutes": 60,
            },
            {
                "start_date": date(2026, 8, 20),
                "interval_days": 14,
                "duration_minutes": 90,
            },
            {
                "start_date": date(2026, 8, 21),
                "interval_days": 7,
                "duration_minutes": 45,
            },
            {
                "start_date": date(2026, 8, 22),
                "interval_days": 21,
                "duration_minutes": 30,
            },
        ]

        # One contract per customer; a customer with multiple locations among
        # the fixtures gets one contract line per location, all under the
        # same contract.
        contracts_by_customer_id: dict[int, Contract] = {}
        lines = []
        for location, fixture in zip(locations, contract_line_fixtures):
            contract = contracts_by_customer_id.get(location.customer_id)
            if contract is None:
                contract = Contract(customer_id=location.customer_id)
                db.add(contract)
                db.flush()
                contracts_by_customer_id[location.customer_id] = contract
            line = ContractLine(
                contract=contract,
                customer_location=location,
                start_date=fixture["start_date"],
                interval_days=fixture["interval_days"],
                duration_minutes=fixture["duration_minutes"],
                required_products=_random_products(products),
            )
            db.add(line)
            lines.append(line)
        db.flush()

        visits = []
        for line in lines:
            for occurrence in range(2):
                visits.append(
                    ServiceVisit(
                        contract_line=line,
                        requested_date=line.start_date
                        + timedelta(days=occurrence * line.interval_days),
                    )
                )
        db.add_all(visits)

        db.commit()
        print(
            f"Synced customers/locations from Tripletex; seeded {len(regions)} regions, "
            f"{len(products)} products, {len(locations)} customer locations, "
            f"{len(contracts_by_customer_id)} contracts, {len(lines)} contract lines, "
            f"{len(employees)} employees, and {len(visits)} service visits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
