from __future__ import annotations

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Employee
from app.schemas import EmployeeRescoSyncResult, RescoSyncSummary


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
