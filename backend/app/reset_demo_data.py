"""Reset and reseed the demo environment.

Deletes every customer and customer location in the connected Tripletex
account (products are left untouched) and their local mirrors, then creates
a fresh ~150-customer demo scenario from bundled CSV data: new Tripletex
customers/delivery addresses, synced locally via the existing sync
functions, with local contracts/contract lines/service visits seeded from a
second CSV. Also updates every existing employee's product portfolio.

This is destructive against a live Tripletex account, so it refuses to do
anything unless invoked with --confirm.

Usage: python -m app.reset_demo_data --confirm
"""
import argparse
import csv
from datetime import date
from pathlib import Path

from app.config import settings
from app.database import SessionLocal
from app.geocoding import geocode_address
from app.models import (
    Assignment,
    Contract,
    ContractLine,
    Customer,
    CustomerLocation,
    CustomerLocationSyncLog,
    CustomerSyncLog,
    Employee,
    Product,
    ServiceVisit,
    contract_line_products,
)
from app.tripletex import (
    TripletexAuthError,
    TripletexClient,
    sync_customer_locations,
    sync_customers,
)
from app.visit_generation import generate_occurrence_dates

DEMO_DATA_DIR = Path(__file__).resolve().parent / "demo_data"
CUSTOMERS_CSV = DEMO_DATA_DIR / "customers.csv"
CONTRACT_LINES_CSV = DEMO_DATA_DIR / "contract_lines.csv"

CONTRACT_LINE_INTERVAL_UNIT = "week"
CONTRACT_LINE_INTERVAL_COUNT = 2
CONTRACT_LINE_DURATION_MINUTES = 45
DEMO_PRODUCT_NUMBERS = ["TJN10001", "TJN10002", "TJN10003", "TJN10004"]
HELD_BACK_PRODUCT_NUMBER = "TJN10004"


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _delete_tripletex_data(client: TripletexClient) -> None:
    """Delete every Tripletex customer; each customer's delivery address is
    cascaded away with it (Tripletex has no standalone delivery-address
    delete endpoint). A customer with existing ledger/invoice history (e.g.
    Tripletex's own built-in sample company) may refuse deletion — that is
    logged and skipped rather than aborting the whole reset."""
    customers = client.get_customers()
    deleted = 0
    skipped: list[str] = []
    for customer in customers:
        try:
            client.delete_customer(customer["id"])
            deleted += 1
        except TripletexAuthError as exc:
            skipped.append(f"{customer['id']} ({customer.get('name')}): {exc}")

    print(f"Deleted {deleted}/{len(customers)} Tripletex customer(s).")
    if skipped:
        print(f"Skipped {len(skipped)} customer(s) that could not be deleted:")
        for line in skipped:
            print(f"  - {line}")


def _delete_local_data(db) -> None:
    db.query(Assignment).delete(synchronize_session=False)
    db.query(ServiceVisit).delete(synchronize_session=False)
    db.execute(contract_line_products.delete())
    db.query(ContractLine).delete(synchronize_session=False)
    db.query(Contract).delete(synchronize_session=False)
    db.query(CustomerLocationSyncLog).delete(synchronize_session=False)
    db.query(CustomerLocation).delete(synchronize_session=False)
    db.query(CustomerSyncLog).delete(synchronize_session=False)
    db.query(Customer).delete(synchronize_session=False)
    db.commit()
    print(
        "Hard-deleted local assignments, service visits, contract lines, "
        "contracts, customer/customer-location sync logs, customer "
        "locations, and customers."
    )


def _location_display_address(street: str, postal_code: str | None, city: str | None) -> str:
    locality = " ".join(part for part in [postal_code, city] if part)
    return ", ".join(part for part in [street, locality] if part)


def _create_local_customers(db, rows: list[dict]) -> dict[str, CustomerLocation]:
    """Create each CSV row's customer and its first customer location
    locally (fms_ros-assigned ids, no Tripletex id yet) - pushed to
    Tripletex later, after all local seeding is complete, via the
    bootstrap-sync functions.

    Returns a map of customer_key -> the created CustomerLocation, so
    later seeding steps can use the local objects directly rather than
    re-fetching them by an id.
    """
    customer_key_to_location: dict[str, CustomerLocation] = {}
    for row in rows:
        customer = Customer(name=row["name"])
        db.add(customer)
        db.flush()

        address = _location_display_address(row["street"], row["postal_code"], row["city"])
        location = CustomerLocation(
            customer_id=customer.id,
            address_line_1=row["street"],
            postal_code=row["postal_code"],
            city=row["city"],
            address=address,
        )
        resolved = geocode_address(address)
        if resolved is not None:
            location.latitude, location.longitude = resolved
        db.add(location)
        db.flush()

        customer_key_to_location[row["customer_key"]] = location

    db.commit()
    print(
        f"Created {len(customer_key_to_location)} customer(s) and "
        "customer location(s) locally."
    )
    return customer_key_to_location


def _seed_contracts_and_visits(
    db, contract_line_rows: list[dict], customer_key_to_location: dict[str, CustomerLocation]
) -> None:
    products_by_number = {
        p.number: p
        for p in db.query(Product).filter(Product.number.in_(DEMO_PRODUCT_NUMBERS)).all()
    }

    contracts_by_customer_id: dict[int, Contract] = {}
    today = date.today()
    lines_created = 0
    visits_created = 0

    for row in contract_line_rows:
        location = customer_key_to_location[row["customer_key"]]

        contract = contracts_by_customer_id.get(location.customer_id)
        if contract is None:
            contract = Contract(customer_id=location.customer_id)
            db.add(contract)
            db.flush()
            contracts_by_customer_id[location.customer_id] = contract

        product = products_by_number[row["product_number"]]
        line = ContractLine(
            contract=contract,
            customer_location=location,
            start_date=today,
            end_date=None,
            interval_unit=CONTRACT_LINE_INTERVAL_UNIT,
            interval_count=CONTRACT_LINE_INTERVAL_COUNT,
            duration_minutes=CONTRACT_LINE_DURATION_MINUTES,
            required_products=[product],
        )
        db.add(line)
        db.flush()
        lines_created += 1

        occurrence_dates = generate_occurrence_dates(
            line.start_date, line.interval_unit, line.interval_count, line.end_date
        )
        for occurrence_date in occurrence_dates:
            db.add(ServiceVisit(contract_line_id=line.id, requested_date=occurrence_date))
            visits_created += 1

    db.commit()
    print(
        f"Seeded {len(contracts_by_customer_id)} contract(s), {lines_created} "
        f"contract line(s), and {visits_created} service visit(s)."
    )


def _update_employee_products(db) -> None:
    employees = db.query(Employee).order_by(Employee.id).all()
    if not employees:
        print("No employees present; skipping product portfolio update.")
        return

    products_by_number = {
        p.number: p
        for p in db.query(Product).filter(Product.number.in_(DEMO_PRODUCT_NUMBERS)).all()
    }
    full_set = [products_by_number[n] for n in DEMO_PRODUCT_NUMBERS]
    held_back_set = [
        products_by_number[n] for n in DEMO_PRODUCT_NUMBERS if n != HELD_BACK_PRODUCT_NUMBER
    ]

    for employee in employees[:-1]:
        employee.products = full_set
    employees[-1].products = held_back_set

    db.commit()
    print(
        f"Updated product portfolios for {len(employees)} employee(s); "
        f"employee id={employees[-1].id} is missing {HELD_BACK_PRODUCT_NUMBER}."
    )


def reset_demo_data() -> None:
    customer_rows = _read_csv(CUSTOMERS_CSV)
    contract_line_rows = _read_csv(CONTRACT_LINES_CSV)

    client = TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)
    db = SessionLocal()
    try:
        _delete_tripletex_data(client)
        _delete_local_data(db)

        customer_key_to_location = _create_local_customers(db, customer_rows)
        _seed_contracts_and_visits(db, contract_line_rows, customer_key_to_location)
        _update_employee_products(db)

        # Push everything just seeded to Tripletex/Resco last - local
        # seeding never waited on this, matching the rest of this system's
        # local-first behavior. See local-first-masterdata-sync's design.md.
        sync_customers(db)
        sync_customer_locations(db)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the destructive reset and reseed. Without this flag, nothing is touched.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "This would delete ALL customers and customer locations in the "
            "connected Tripletex account and the local database, then "
            f"reseed ~{len(_read_csv(CUSTOMERS_CSV))} demo customers, their "
            "contracts/contract lines/service visits, and update every "
            "employee's product portfolio.\n"
            "No Tripletex or database changes were made. Re-run with "
            "--confirm to proceed."
        )
        return

    reset_demo_data()


if __name__ == "__main__":
    main()
