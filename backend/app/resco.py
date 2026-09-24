from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Assignment, Customer, CustomerLocation, Employee, Product, RescoDraftReset, VisitStatus
from app.schemas import (
    AssignmentRescoSyncResult,
    CustomerLocationRescoSyncResult,
    CustomerRescoSyncResult,
    EmployeeRescoSyncResult,
    ProductRescoSyncResult,
    RescoSyncSummary,
    RescoStatusSyncSummary,
)


class RescoAuthError(RuntimeError):
    pass


class RescoApiError(RuntimeError):
    pass


# This codebase's datetimes are otherwise naive throughout - this is the one
# place a wall-clock time crosses into an external API that requires an
# explicit, DST-aware UTC offset (Resco's Edm.DateTimeOffset fields).
_LOCAL_TZ = ZoneInfo("Europe/Oslo")


def _to_resco_datetime(dt: datetime) -> str:
    return dt.replace(tzinfo=_LOCAL_TZ).isoformat()


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
                if not loc.delete_flag and not loc.archived and loc.address_line_1
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

    def _request(self, method: str, entity: str, **kwargs) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.request(
                method, f"{self._base_url}/{entity}", auth=self._auth(), **kwargs
            )
        if response.status_code >= 400:
            raise RescoApiError(f"Resco {entity} failed: {response.status_code} {response.text}")
        return response.json() if response.content else {}

    @staticmethod
    def _functional_location_payload(location: CustomerLocation) -> dict:
        payload = {
            "name": location.address[:160],
            "resco_address_line1": location.address_line_1,
            "resco_address_line2": location.address_line_2,
            "resco_address_postalcode": location.postal_code,
            "resco_address_city": location.city,
            "resco_address_country": (location.country or {}).get("name"),
        }
        if location.latitude is not None and location.longitude is not None:
            payload.update(resco_latitude=location.latitude, resco_longitude=location.longitude)
        return payload

    def create_functional_location(self, location: CustomerLocation) -> dict:
        return self._request("POST", "resco_functionallocation",
                             json=self._functional_location_payload(location))

    def update_functional_location(self, location: CustomerLocation) -> dict:
        payload = {"resco_latitude": None, "resco_longitude": None,
                   **self._functional_location_payload(location)}
        return self._request("PATCH",
                             f"resco_functionallocation('{location.resco_functional_location_id}')",
                             json=payload)

    @staticmethod
    def _asset_payload(location: CustomerLocation) -> dict:
        return {
            "name": location.address[:160],
            "customerid_account@odata.bind": f"/account({location.customer.resco_account_id})",
            "resco_functionallocationid_resco_functionallocation@odata.bind":
                f"/resco_functionallocation({location.resco_functional_location_id})",
        }

    def create_asset(self, location: CustomerLocation) -> dict:
        return self._request("POST", "fs_asset", json=self._asset_payload(location))

    def update_asset(self, location: CustomerLocation) -> dict:
        return self._request("PATCH", f"fs_asset('{location.resco_asset_id}')",
                             json=self._asset_payload(location))

    @staticmethod
    def _contact_payload(customer: Customer) -> dict:
        return {
            "firstname": None,
            "lastname": customer.contact_name,
            "emailaddress1": customer.email,
            "telephone1": customer.phone_number,
            "mobilephone": customer.phone_number_mobile,
            "parentcustomerid_account@odata.bind": f"/account({customer.resco_account_id})",
        }

    def create_contact(self, customer: Customer) -> dict:
        return self._request("POST", "contact", json=self._contact_payload(customer))

    def update_contact(self, customer: Customer) -> dict:
        return self._request("PATCH", f"contact('{customer.resco_contact_id}')",
                             json=self._contact_payload(customer))

    def link_contact(self, customer: Customer) -> dict:
        return self._request("PATCH", f"account('{customer.resco_account_id}')", json={
            "primarycontactid_contact@odata.bind": f"/contact({customer.resco_contact_id})",
        })

    @staticmethod
    def _product_payload(product: Product) -> dict:
        return {"name": product.name, "productnumber": product.number}

    def create_product(self, product: Product) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/product",
                auth=self._auth(),
                json=self._product_payload(product),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco product create failed: {response.status_code} {response.text}"
            )
        return response.json()

    def update_product(self, product: Product) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.patch(
                f"{self._base_url}/product('{product.resco_product_id}')",
                auth=self._auth(),
                json=self._product_payload(product),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco product update failed: {response.status_code} {response.text}"
            )
        return response.json()

    def find_resource_id_for_user(self, resco_user_id: str) -> str:
        """The fs_resource Resco auto-provisions for a systemuser the moment
        that user is created - this system never creates or manages
        fs_resource records itself, only looks up the one that already
        exists for a synced employee."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.get(
                f"{self._base_url}/fs_resource",
                auth=self._auth(),
                params={"$filter": f"__targetid_id eq '{resco_user_id}'"},
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco resource lookup failed: {response.status_code} {response.text}"
            )
        matches = response.json()["value"]
        if len(matches) != 1:
            raise RescoApiError(
                f"Expected exactly one Resco resource for user {resco_user_id}, found {len(matches)}"
            )
        return matches[0]["id"]

    @staticmethod
    def _work_order_payload(assignment: Assignment) -> dict:
        location = assignment.service_visit.contract_line.customer_location
        suffix = f" | Visit {assignment.service_visit_id}"
        name = f"{location.customer.name}: {location.address}"
        return {
            "name": name[:160 - len(suffix)] + suffix,
            "customerid_account@odata.bind": f"/account({location.customer.resco_account_id})",
            "fs_assetid_fs_asset@odata.bind": f"/fs_asset({location.resco_asset_id})",
        }

    def create_work_order(self, assignment: Assignment) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/fs_workorder",
                auth=self._auth(),
                json={**self._work_order_payload(assignment), "statecode": 0, "statuscode": 5},
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco work order create failed: {response.status_code} {response.text}"
            )
        return response.json()

    def update_work_order(self, assignment: Assignment) -> dict:
        # Updating names or bindings must never overwrite field progress.
        return self._request("PATCH", f"fs_workorder('{assignment.resco_work_order_id}')",
                             json=self._work_order_payload(assignment))

    def get_work_order_status(self, work_order_id: str) -> dict:
        return self._request("GET", f"fs_workorder('{work_order_id}')",
                             params={"$select": "id,statecode,statuscode"},
                             headers={"Prefer": 'odata.include-annotations="*"'})

    @staticmethod
    def _work_order_schedule_payload(assignment: Assignment, resource_id: str) -> dict:
        return {
            "scheduledstart": _to_resco_datetime(assignment.planned_start),
            "scheduledend": _to_resco_datetime(assignment.planned_end),
            "resourceid_fs_resource@odata.bind": f"/fs_resource({resource_id})",
        }

    def create_work_order_schedule(
        self, assignment: Assignment, work_order_id: str, resource_id: str
    ) -> dict:
        payload = self._work_order_schedule_payload(assignment, resource_id)
        payload["workorderid_fs_workorder@odata.bind"] = f"/fs_workorder({work_order_id})"
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/fs_workorderschedule",
                auth=self._auth(),
                json=payload,
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco work order schedule create failed: {response.status_code} {response.text}"
            )
        return response.json()

    def update_work_order_schedule(self, assignment: Assignment, resource_id: str) -> dict:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.patch(
                f"{self._base_url}/fs_workorderschedule('{assignment.resco_work_order_schedule_id}')",
                auth=self._auth(),
                json=self._work_order_schedule_payload(assignment, resource_id),
            )
        if response.status_code >= 400:
            raise RescoApiError(
                f"Resco work order schedule update failed: {response.status_code} {response.text}"
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
        if customer.resco_contact_id:
            client.update_contact(customer)
        elif customer.contact_name or customer.phone_number_mobile:
            data = client.create_contact(customer)
            customer.resco_contact_id = str(data["id"])
            db.add(customer)
            db.commit()
        if customer.resco_contact_id:
            client.link_contact(customer)
    except Exception as exc:
        return CustomerRescoSyncResult(status="failed", detail=str(exc))

    return CustomerRescoSyncResult(status="synced")


def sync_customers_to_resco(db: Session) -> RescoSyncSummary:
    customers = (
        db.query(Customer)
        .filter(Customer.delete_flag.is_(False), Customer.archived.is_(False))
        .all()
    )

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
        if location.resco_functional_location_id:
            client.update_functional_location(location)
        else:
            data = client.create_functional_location(location)
            location.resco_functional_location_id = str(data["id"])
            db.add(location)
            db.commit()
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
        db.query(CustomerLocation)
        .join(CustomerLocation.customer)
        .filter(CustomerLocation.delete_flag.is_(False), CustomerLocation.archived.is_(False),
                Customer.delete_flag.is_(False), Customer.archived.is_(False))
        .all()
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


def sync_product(db: Session, product: Product) -> ProductRescoSyncResult:
    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    try:
        if product.resco_product_id:
            client.update_product(product)
        else:
            data = client.create_product(product)
            product.resco_product_id = str(data["id"])
            db.add(product)
            db.commit()
    except Exception as exc:
        return ProductRescoSyncResult(status="failed", detail=str(exc))

    return ProductRescoSyncResult(status="synced")


def sync_products_to_resco(db: Session) -> RescoSyncSummary:
    products = (
        db.query(Product)
        .filter(Product.delete_flag.is_(False), Product.archived.is_(False))
        .all()
    )

    created = 0
    updated = 0
    failed = 0
    errors: list[str] = []

    for product in products:
        was_new = product.resco_product_id is None
        result = sync_product(db, product)
        if result.status == "synced":
            if was_new:
                created += 1
            else:
                updated += 1
        else:
            failed += 1
            if result.detail:
                errors.append(f"{product.name}: {result.detail}")

    return RescoSyncSummary(created=created, updated=updated, skipped=0, failed=failed, errors=errors)


def sync_assignment(db: Session, assignment: Assignment) -> AssignmentRescoSyncResult:
    employee = assignment.employee
    location = assignment.service_visit.contract_line.customer_location

    if not employee.resco_user_id:
        return AssignmentRescoSyncResult(status="skipped", detail="Employee not yet synced to Resco")
    if not (location.resco_asset_id and location.resco_functional_location_id
            and location.customer.resco_account_id):
        return AssignmentRescoSyncResult(
            status="skipped", detail="Customer location not yet synced to Resco"
        )

    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    try:
        resource_id = client.find_resource_id_for_user(employee.resco_user_id)
        if assignment.resco_work_order_id:
            client.update_work_order(assignment)
        else:
            work_order = client.create_work_order(assignment)
            assignment.resco_work_order_id = str(work_order["id"])
            db.add(assignment)
            db.commit()
        if assignment.resco_work_order_schedule_id:
            client.update_work_order_schedule(assignment, resource_id)
        else:
            schedule = client.create_work_order_schedule(
                assignment, assignment.resco_work_order_id, resource_id
            )
            assignment.resco_work_order_schedule_id = str(schedule["id"])
            db.add(assignment)
            db.commit()
    except Exception as exc:
        return AssignmentRescoSyncResult(status="failed", detail=str(exc))

    return AssignmentRescoSyncResult(status="synced")


def _is_resco_status_completed(statecode: int | None) -> bool:
    return statecode == 1


def _retry_draft_resets(db: Session, client: RescoClient, summary: RescoStatusSyncSummary) -> None:
    for reset in db.query(RescoDraftReset).filter(RescoDraftReset.status == "pending").all():
        try:
            data = client.get_work_order_status(reset.work_order_id)
            codes = (data.get("statecode"), data.get("statuscode"))
            if any(type(code) is not int for code in codes):
                raise RescoApiError("Work Order response missing numeric state/status")
            if codes == (0, 1):
                reset.status = "completed"
            elif codes != (0, 5) or db.query(Assignment).filter(
                Assignment.resco_work_order_id == reset.work_order_id
            ).first() is not None:
                reset.status = "cancelled"
                summary.reconciliation_skipped += 1
                summary.skip_reasons.append(
                    f"Visit {reset.service_visit_id}: Draft reset cancelled; Work Order progressed or was reassigned"
                )
            else:
                # Conditional updates protect changes made between the fresh read and reset.
                etag = data.get("@odata.etag")
                if not etag:
                    raise RescoApiError("Missing Work Order ETag; Draft reset deferred")
                client._request("PATCH", f"fs_workorder('{reset.work_order_id}')",
                                json={"statecode": 0, "statuscode": 1},
                                headers={"If-Match": etag})
                reset.status = "completed"
            reset.last_error = None
            db.commit()
        except Exception as exc:
            db.rollback()
            reset.last_error = str(exc)
            db.commit()
            summary.reset_failed += 1
            summary.errors.append(f"Visit {reset.service_visit_id}: Draft reset failed: {exc}")


def sync_assignment_statuses_from_resco(db: Session) -> RescoStatusSyncSummary:
    summary = RescoStatusSyncSummary()
    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    for assignment in db.query(Assignment).all():
        visit_id = assignment.service_visit_id
        if not assignment.resco_work_order_id:
            summary.skipped += 1
            continue
        try:
            data = client.get_work_order_status(assignment.resco_work_order_id)
            statecode, statuscode = data.get("statecode"), data.get("statuscode")
            if type(statecode) is not int or type(statuscode) is not int:
                raise RescoApiError("Work Order response missing numeric state/status")
            assignment.resco_statecode = statecode
            assignment.resco_statuscode = statuscode
            assignment.resco_status = data.get("statuscode@RescoCloud.FormattedValue") or str(statuscode)
            db.commit()
            summary.pulled += 1
            if assignment.planned_start.date() < date.today() and (statecode, statuscode) == (0, 5):
                reset = RescoDraftReset(
                    work_order_id=assignment.resco_work_order_id, service_visit_id=visit_id,
                    schedule_id=assignment.resco_work_order_schedule_id,
                    planned_start=assignment.planned_start, status="pending",
                )
                visit = assignment.service_visit
                visit.status = VisitStatus.UNASSIGNED
                visit.unassigned_reason = "Past planned visit still Scheduled in Resco"
                assignment.pinned = False
                db.add(reset)
                db.delete(assignment)
                db.commit()
                summary.reconciled += 1
        except Exception as exc:
            db.rollback()
            summary.failed += 1
            summary.errors.append(f"Visit {visit_id}: {exc}")
    _retry_draft_resets(db, client, summary)
    return summary
