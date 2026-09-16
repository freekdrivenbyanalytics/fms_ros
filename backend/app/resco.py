from __future__ import annotations

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Customer, CustomerLocation, Employee
from app.schemas import (
    CustomerLocationRescoSyncResult,
    CustomerRescoSyncResult,
    EmployeeRescoSyncResult,
    RescoSyncSummary,
)


class RescoAuthError(RuntimeError):
    pass


class RescoApiError(RuntimeError):
    pass


class RescoClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password

    def _auth(self) -> httpx.BasicAuth:
        if not self._username or not self._password:
            raise RescoAuthError(
                "Resco credentials not configured - set RESCO_USERNAME and "
                "RESCO_PASSWORD in backend/.env"
            )
        return httpx.BasicAuth(username=self._username, password=self._password)

    @staticmethod
    def _user_payload(employee: Employee) -> dict:
        return {
            "firstname": employee.first_name,
            "lastname": employee.last_name,
            "internalemailaddress": employee.email,
            "mobilephone": employee.mobile_phone,
        }

    def create_user(self, employee: Employee) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/systemuser",
                auth=self._auth(),
                json=self._user_payload(employee),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco user create failed: {response.status_code} {response.text}"
            )
        return response.json()

    def update_user(self, employee: Employee) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.patch(
                f"{self._base_url}/systemuser('{employee.resco_user_id}')",
                auth=self._auth(),
                json=self._user_payload(employee),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco user update failed: {response.status_code} {response.text}"
            )
        return response.json()

    @staticmethod
    def _account_payload(customer: Customer) -> dict:
        location = next(
            (
                loc
                for loc in customer.locations
                if not loc.delete_flag and loc.address_line_1
            ),
            None,
        )
        country = (location.country or {}) if location else {}
        return {
            "name": customer.name,
            "emailaddress1": customer.email,
            "telephone1": customer.phone_number,
            "vatid": customer.organization_number,
            "address1_line1": location.address_line_1 if location else None,
            "address1_city": location.city if location else None,
            "address1_postalcode": location.postal_code if location else None,
            "address1_country": country.get("name"),
        }

    def create_account(self, customer: Customer) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/account",
                auth=self._auth(),
                json=self._account_payload(customer),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco account create failed: {response.status_code} {response.text}"
            )
        return response.json()

    def update_account(self, customer: Customer) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.patch(
                f"{self._base_url}/account('{customer.resco_account_id}')",
                auth=self._auth(),
                json=self._account_payload(customer),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco account update failed: {response.status_code} {response.text}"
            )
        return response.json()

    def create_asset(self, location: CustomerLocation) -> dict:
        payload = {
            "name": location.address,
            "customerid_account@odata.bind": f"/account({location.customer.resco_account_id})",
        }
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/fs_asset",
                auth=self._auth(),
                json=payload,
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco asset create failed: {response.status_code} {response.text}"
            )
        return response.json()

    def update_asset(self, location: CustomerLocation) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.patch(
                f"{self._base_url}/fs_asset('{location.resco_asset_id}')",
                auth=self._auth(),
                json={"name": location.address},
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco asset update failed: {response.status_code} {response.text}"
            )
        return response.json()


def sync_employee(db: Session, employee: Employee) -> EmployeeRescoSyncResult:
    if not employee.email or not employee.mobile_phone:
        return EmployeeRescoSyncResult(
            status="skipped", detail="Missing email or mobile phone"
        )

    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    try:
        if employee.resco_user_id:
            client.update_user(employee)
        else:
            data = client.create_user(employee)
            employee.resco_user_id = str(data["id"])
            db.add(employee)
            db.commit()
    except Exception as exc:
        return EmployeeRescoSyncResult(status="failed", detail=str(exc))

    return EmployeeRescoSyncResult(status="synced")


def sync_all_employees(db: Session) -> RescoSyncSummary:
    employees = db.query(Employee).filter(Employee.delete_flag.is_(False)).all()

    created = 0
    updated = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    for employee in employees:
        was_new = employee.resco_user_id is None
        result = sync_employee(db, employee)
        if result.status == "synced":
            if was_new:
                created += 1
            else:
                updated += 1
        elif result.status == "skipped":
            skipped += 1
        else:
            failed += 1
            if result.detail:
                errors.append(f"{employee.name}: {result.detail}")

    return RescoSyncSummary(
        created=created, updated=updated, skipped=skipped, failed=failed, errors=errors
    )


def sync_customer(db: Session, customer: Customer) -> CustomerRescoSyncResult:
    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    try:
        if customer.resco_account_id:
            client.update_account(customer)
        else:
            data = client.create_account(customer)
            customer.resco_account_id = str(data["id"])
            db.add(customer)
            db.commit()
    except Exception as exc:
        return CustomerRescoSyncResult(status="failed", detail=str(exc))

    return CustomerRescoSyncResult(status="synced")


def sync_customers_to_resco(db: Session) -> RescoSyncSummary:
    customers = db.query(Customer).filter(Customer.delete_flag.is_(False)).all()

    created = 0
    updated = 0
    failed = 0
    errors: list[str] = []

    for customer in customers:
        was_new = customer.resco_account_id is None
        result = sync_customer(db, customer)
        if result.status == "synced":
            if was_new:
                created += 1
            else:
                updated += 1
        else:
            failed += 1
            if result.detail:
                errors.append(f"{customer.name}: {result.detail}")

    return RescoSyncSummary(created=created, updated=updated, skipped=0, failed=failed, errors=errors)


def sync_customer_location(db: Session, location: CustomerLocation) -> CustomerLocationRescoSyncResult:
    if not location.address_line_1:
        return CustomerLocationRescoSyncResult(status="skipped", detail="No street address")

    if not location.customer.resco_account_id:
        return CustomerLocationRescoSyncResult(
            status="skipped", detail="Customer not yet synced to Resco"
        )

    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    try:
        if location.resco_asset_id:
            client.update_asset(location)
        else:
            data = client.create_asset(location)
            location.resco_asset_id = str(data["id"])
            db.add(location)
            db.commit()
    except Exception as exc:
        return CustomerLocationRescoSyncResult(status="failed", detail=str(exc))

    return CustomerLocationRescoSyncResult(status="synced")


def sync_customer_locations_to_resco(db: Session) -> RescoSyncSummary:
    locations = (
        db.query(CustomerLocation).filter(CustomerLocation.delete_flag.is_(False)).all()
    )

    created = 0
    updated = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    for location in locations:
        was_new = location.resco_asset_id is None
        result = sync_customer_location(db, location)
        if result.status == "synced":
            if was_new:
                created += 1
            else:
                updated += 1
        elif result.status == "skipped":
            skipped += 1
        else:
            failed += 1
            if result.detail:
                errors.append(f"{location.address}: {result.detail}")

    return RescoSyncSummary(
        created=created, updated=updated, skipped=skipped, failed=failed, errors=errors
    )
