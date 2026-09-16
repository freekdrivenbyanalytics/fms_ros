"""One-time script: seed this sandbox's existing Tripletex customers with
contact/org-number data from tripletex_customer_contacts.csv.

Not part of seed.py or backend startup - run manually, once, from the
backend directory:

    .venv/Scripts/python.exe scripts/seed_tripletex_customer_contacts.py

IMPORTANT: do NOT add `physicalAddress` to the update payload below. An
earlier version of this script did, and discovered the hard way that
Tripletex's customer PUT treats a `physicalAddress` object as creating a
brand-new delivery address (customer location) as a side effect, rather
than just updating the customer's own address in place - this duplicated
every customer's real location with an unwanted extra one. The CSV's
address/postal_code/city columns are unused for that reason; the Resco
Account's address is sourced from the customer's existing customer_location
instead (see app/resco.py).
"""

import csv
from pathlib import Path

from app.config import settings
from app.tripletex import TripletexAuthError, TripletexClient

CSV_PATH = Path(__file__).resolve().parent / "tripletex_customer_contacts.csv"


def main() -> None:
    client = TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)

    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    succeeded = 0
    failed: list[tuple[str, str]] = []

    for row in rows:
        customer_id = int(row["customer_id"])
        try:
            client.update_customer(
                customer_id,
                {
                    "email": row["email"],
                    "phoneNumber": row["phone_number"],
                    "organizationNumber": row["organization_number"],
                },
            )
            succeeded += 1
        except TripletexAuthError as exc:
            failed.append((row["customer_id"], str(exc)))

    print(f"Seeded {succeeded}/{len(rows)} customers")
    if failed:
        print(f"{len(failed)} failed:")
        for customer_id, error in failed:
            print(f"  {customer_id}: {error}")


if __name__ == "__main__":
    main()
