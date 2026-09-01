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
            employee_fixtures = [
                {
                    "name": "Alice Johnson",
                    "work_start": time(8, 0),
                    "work_end": time(16, 0),
                    "latitude": 52.3676,
                    "longitude": 4.9041,
                    "regions": [north_holland, utrecht],
                    "skills": [electrical, general_maintenance],
                },
                {
                    "name": "Bram de Vries",
                    "work_start": time(9, 0),
                    "work_end": time(17, 0),
                    "latitude": 52.0907,
                    "longitude": 5.1214,
                    "regions": [utrecht],
                    "skills": [plumbing],
                },
                {
                    "name": "Chen Wei",
                    "work_start": time(7, 30),
                    "work_end": time(15, 30),
                    "latitude": 51.9244,
                    "longitude": 4.4777,
                    "regions": [south_holland, groningen],
                    "skills": [hvac, general_maintenance],
                },
            ]
            for fixture in employee_fixtures:
                employee = Employee(
                    name=fixture["name"],
                    latitude=fixture["latitude"],
                    longitude=fixture["longitude"],
                    regions=fixture["regions"],
                    skills=fixture["skills"],
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

        contract_line_fixtures = [
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
                required_skills=fixture["required_skills"],
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
            f"{len(skills)} skills, {len(locations)} customer locations, "
            f"{len(contracts_by_customer_id)} contracts, {len(lines)} contract lines, "
            f"{len(employees)} employees, and {len(visits)} service visits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
