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


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Employee).count() or db.query(ServiceVisit).count():
            print("Seed data already present, skipping.")
            return

        north_holland = Region(name="North Holland")
        utrecht = Region(name="Utrecht")
        south_holland = Region(name="South Holland")
        groningen = Region(name="Groningen")
        regions = [north_holland, utrecht, south_holland, groningen]
        db.add_all(regions)

        plumbing = Skill(name="Plumbing")
        electrical = Skill(name="Electrical")
        hvac = Skill(name="HVAC")
        general_maintenance = Skill(name="General Maintenance")
        skills = [plumbing, electrical, hvac, general_maintenance]
        db.add_all(skills)
        db.flush()

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

        van_der_berg = Customer(name="Van der Berg Household")
        bakker = Customer(name="Bakker Family")
        de_jong = Customer(name="De Jong Office")
        visser = Customer(name="Visser Residence")
        customers = [van_der_berg, bakker, de_jong, visser]
        db.add_all(customers)
        db.flush()

        van_der_berg_location = CustomerLocation(
            customer=van_der_berg,
            region=north_holland,
            address="Prinsengracht 12, Amsterdam",
            latitude=52.3738,
            longitude=4.8910,
        )
        bakker_location = CustomerLocation(
            customer=bakker,
            region=utrecht,
            address="Neude 5, Utrecht",
            latitude=52.0925,
            longitude=5.1197,
        )
        de_jong_hq = CustomerLocation(
            customer=de_jong,
            region=south_holland,
            address="Coolsingel 40, Rotterdam",
            latitude=51.9233,
            longitude=4.4792,
        )
        de_jong_branch = CustomerLocation(
            customer=de_jong,
            region=south_holland,
            address="Blaak 10, Rotterdam",
            latitude=51.9214,
            longitude=4.4886,
        )
        visser_location = CustomerLocation(
            customer=visser,
            region=groningen,
            address="Grote Markt 1, Groningen",
            latitude=53.2194,
            longitude=6.5665,
        )
        locations = [
            van_der_berg_location,
            bakker_location,
            de_jong_hq,
            de_jong_branch,
            visser_location,
        ]
        db.add_all(locations)
        db.flush()

        contracts = [
            Contract(
                customer_location=van_der_berg_location,
                start_date=date(2026, 8, 20),
                interval_days=30,
                duration_minutes=60,
                required_skills=[general_maintenance],
            ),
            Contract(
                customer_location=bakker_location,
                start_date=date(2026, 8, 20),
                interval_days=14,
                duration_minutes=90,
                required_skills=[plumbing],
            ),
            Contract(
                customer_location=de_jong_hq,
                start_date=date(2026, 8, 21),
                interval_days=7,
                duration_minutes=45,
                required_skills=[electrical],
            ),
            Contract(
                customer_location=de_jong_branch,
                start_date=date(2026, 8, 22),
                interval_days=21,
                duration_minutes=30,
                required_skills=[hvac, general_maintenance],
            ),
            Contract(
                customer_location=visser_location,
                start_date=date(2026, 8, 21),
                interval_days=60,
                duration_minutes=120,
                required_skills=[hvac],
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
            f"Seeded {len(regions)} regions, {len(skills)} skills, "
            f"{len(customers)} customers, {len(locations)} customer locations, "
            f"{len(contracts)} contracts, {len(employees)} employees, "
            f"and {len(visits)} service visits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
