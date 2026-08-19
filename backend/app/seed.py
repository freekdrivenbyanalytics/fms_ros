from datetime import date, time

from app.database import SessionLocal
from app.models import Employee, ServiceVisit


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Employee).count() or db.query(ServiceVisit).count():
            print("Seed data already present, skipping.")
            return

        employees = [
            Employee(
                name="Alice Johnson",
                work_start=time(8, 0),
                work_end=time(16, 0),
                latitude=52.3676,
                longitude=4.9041,
            ),
            Employee(
                name="Bram de Vries",
                work_start=time(9, 0),
                work_end=time(17, 0),
                latitude=52.0907,
                longitude=5.1214,
            ),
            Employee(
                name="Chen Wei",
                work_start=time(7, 30),
                work_end=time(15, 30),
                latitude=51.9244,
                longitude=4.4777,
            ),
        ]
        db.add_all(employees)

        visits = [
            ServiceVisit(
                customer_name="Van der Berg Household",
                address="Prinsengracht 12, Amsterdam",
                latitude=52.3738,
                longitude=4.8910,
                duration_minutes=60,
                requested_date=date(2026, 8, 20),
            ),
            ServiceVisit(
                customer_name="Bakker Family",
                address="Neude 5, Utrecht",
                latitude=52.0925,
                longitude=5.1197,
                duration_minutes=90,
                requested_date=date(2026, 8, 20),
            ),
            ServiceVisit(
                customer_name="De Jong Office",
                address="Coolsingel 40, Rotterdam",
                latitude=51.9233,
                longitude=4.4792,
                duration_minutes=45,
                requested_date=date(2026, 8, 21),
            ),
            ServiceVisit(
                customer_name="Visser Residence",
                address="Grote Markt 1, Groningen",
                latitude=53.2194,
                longitude=6.5665,
                duration_minutes=120,
                requested_date=date(2026, 8, 21),
            ),
        ]
        db.add_all(visits)

        db.commit()
        print(f"Seeded {len(employees)} employees and {len(visits)} service visits.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
