from datetime import date, time

from app.database import SessionLocal
from app.models import Customer, CustomerLocation, Employee, Region, ServiceVisit


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
        db.flush()

        employees = [
            Employee(
                name="Alice Johnson",
                work_start=time(8, 0),
                work_end=time(16, 0),
                latitude=52.3676,
                longitude=4.9041,
                regions=[north_holland, utrecht],
            ),
            Employee(
                name="Bram de Vries",
                work_start=time(9, 0),
                work_end=time(17, 0),
                latitude=52.0907,
                longitude=5.1214,
                regions=[utrecht],
            ),
            Employee(
                name="Chen Wei",
                work_start=time(7, 30),
                work_end=time(15, 30),
                latitude=51.9244,
                longitude=4.4777,
                regions=[south_holland, groningen],
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

        visits = [
            ServiceVisit(
                customer_location=van_der_berg_location,
                duration_minutes=60,
                requested_date=date(2026, 8, 20),
            ),
            ServiceVisit(
                customer_location=bakker_location,
                duration_minutes=90,
                requested_date=date(2026, 8, 20),
            ),
            ServiceVisit(
                customer_location=de_jong_hq,
                duration_minutes=45,
                requested_date=date(2026, 8, 21),
            ),
            ServiceVisit(
                customer_location=de_jong_branch,
                duration_minutes=30,
                requested_date=date(2026, 8, 22),
            ),
            ServiceVisit(
                customer_location=visser_location,
                duration_minutes=120,
                requested_date=date(2026, 8, 21),
            ),
        ]
        db.add_all(visits)

        db.commit()
        print(
            f"Seeded {len(regions)} regions, {len(customers)} customers, "
            f"{len(locations)} customer locations, {len(employees)} employees, "
            f"and {len(visits)} service visits."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
