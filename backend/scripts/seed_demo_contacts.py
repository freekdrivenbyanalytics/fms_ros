"""Fill missing contact fields on existing CSV demo customers; never sync externally."""
import csv
from pathlib import Path

from app.database import SessionLocal
from app.models import Customer


def fill_missing_contacts(customer: Customer, key: str) -> bool:
    changed = False
    values = {
        "contact_name": f"Demo Contact {key}",
        "email": f"{key}@example.invalid",
        "phone_number": "00000000",
        "phone_number_mobile": "00000001",
    }
    for field, value in values.items():
        if not getattr(customer, field):
            setattr(customer, field, value)
            changed = True
    return changed


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "app" / "demo_data" / "customers.csv"
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    updated = 0
    with SessionLocal() as db:
        for row in rows:
            matches = db.query(Customer).filter(
                Customer.name == row["name"], Customer.delete_flag.is_(False),
                Customer.archived.is_(False),
            ).all()
            if len(matches) != 1:
                continue
            if fill_missing_contacts(matches[0], row["customer_key"]):
                updated += 1
        db.commit()
    print(f"Filled missing demo contacts for {updated} customers; no external sync performed.")


if __name__ == "__main__":
    main()
