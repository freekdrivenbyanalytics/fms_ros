from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Customer, CustomerChangeType, CustomerSyncLog

API_KEY_PATH = Path(__file__).resolve().parent.parent / ".local" / "api_key"

_SESSION_EXPIRY_MARGIN_SECONDS = 60

_SCALAR_FIELD_MAP = {
    "version": "version",
    "url": "url",
    "name": "name",
    "organizationNumber": "organization_number",
    "globalLocationNumber": "global_location_number",
    "supplierNumber": "supplier_number",
    "customerNumber": "customer_number",
    "isSupplier": "is_supplier",
    "isCustomer": "is_customer",
    "isInactive": "is_inactive",
    "email": "email",
    "invoiceEmail": "invoice_email",
    "overdueNoticeEmail": "overdue_notice_email",
    "phoneNumber": "phone_number",
    "phoneNumberMobile": "phone_number_mobile",
    "description": "description",
    "language": "language",
    "displayName": "display_name",
    "isPrivateIndividual": "is_private_individual",
    "singleCustomerInvoice": "single_customer_invoice",
    "invoiceSendMethod": "invoice_send_method",
    "emailAttachmentType": "email_attachment_type",
    "invoicesDueIn": "invoices_due_in",
    "invoicesDueInType": "invoices_due_in_type",
    "isFactoring": "is_factoring",
    "invoiceSendSMSNotification": "invoice_send_sms_notification",
    "invoiceSMSNotificationNumber": "invoice_sms_notification_number",
    "isAutomaticSoftReminderEnabled": "is_automatic_soft_reminder_enabled",
    "isAutomaticReminderEnabled": "is_automatic_reminder_enabled",
    "isAutomaticNoticeOfDebtCollectionEnabled": (
        "is_automatic_notice_of_debt_collection_enabled"
    ),
    "discountPercentage": "discount_percentage",
    "website": "website",
    "accountManager": "account_manager",
    "department": "department",
    "postalAddress": "postal_address",
    "physicalAddress": "physical_address",
    "deliveryAddress": "delivery_address",
    "category1": "category1",
    "category2": "category2",
    "category3": "category3",
    "currency": "currency",
    "ledgerAccount": "ledger_account",
    "bankAccountPresentation": "bank_account_presentation",
}


class TripletexAuthError(RuntimeError):
    pass


class TripletexClient:
    def __init__(self, base_url: str, session_ttl_seconds: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._session_ttl_seconds = session_ttl_seconds
        self._session_token: str | None = None
        self._session_expires_at: datetime | None = None

    def _read_refresh_token(self) -> str:
        if not API_KEY_PATH.exists():
            raise TripletexAuthError(
                f"Tripletex refresh token not found at {API_KEY_PATH}"
            )
        token = API_KEY_PATH.read_text(encoding="utf-8").strip()
        if not token:
            raise TripletexAuthError(f"Tripletex refresh token at {API_KEY_PATH} is empty")
        return token

    def _exchange_session_token(self) -> str:
        refresh_token = self._read_refresh_token()
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            response = client.post(
                f"{self._base_url}/token/session/:createFromRefreshToken",
                json={
                    "refreshToken": refresh_token,
                    "ttlSeconds": self._session_ttl_seconds,
                },
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex session token exchange failed: {response.status_code} {response.text}"
            )
        payload = response.json()
        token = payload["value"]["token"]
        self._session_token = token
        self._session_expires_at = datetime.now() + timedelta(
            seconds=max(self._session_ttl_seconds - _SESSION_EXPIRY_MARGIN_SECONDS, 0)
        )
        return token

    def _get_session_token(self) -> str:
        if self._session_token is None or (
            self._session_expires_at is not None
            and datetime.now() >= self._session_expires_at
        ):
            return self._exchange_session_token()
        return self._session_token

    def _auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth(username="0", password=self._get_session_token())

    def get_customers(self) -> list[dict]:
        page_size = 100
        offset = 0
        customers: list[dict] = []

        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            while True:
                response = client.get(
                    f"{self._base_url}/customer",
                    auth=self._auth(),
                    params={"from": offset, "count": page_size},
                )
                if response.status_code >= 400:
                    raise TripletexAuthError(
                        f"Tripletex customer fetch failed: {response.status_code} {response.text}"
                    )
                body = response.json()
                page = body["values"]
                customers.extend(page)
                if len(page) < page_size or len(customers) >= body["fullResultSize"]:
                    break
                offset += page_size

        return customers


def _apply_fields(customer: Customer, data: dict) -> bool:
    changed = False
    for tripletex_key, attr in _SCALAR_FIELD_MAP.items():
        new_value = data.get(tripletex_key)
        if getattr(customer, attr) != new_value:
            setattr(customer, attr, new_value)
            changed = True
    return changed


def sync_customers(db: Session) -> None:
    client = TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)
    tripletex_customers = client.get_customers()
    tripletex_ids = {data["id"] for data in tripletex_customers}

    existing = {customer.id: customer for customer in db.query(Customer).all()}

    for data in tripletex_customers:
        customer_id = data["id"]
        customer = existing.get(customer_id)

        if customer is None:
            customer = Customer(id=customer_id)
            _apply_fields(customer, data)
            customer.delete_flag = False
            db.add(customer)
            db.add(
                CustomerSyncLog(
                    customer_id=customer_id, change_type=CustomerChangeType.CREATED
                )
            )
        elif customer.delete_flag:
            _apply_fields(customer, data)
            customer.delete_flag = False
            db.add(
                CustomerSyncLog(
                    customer_id=customer_id, change_type=CustomerChangeType.RESTORED
                )
            )
        elif _apply_fields(customer, data):
            db.add(
                CustomerSyncLog(
                    customer_id=customer_id, change_type=CustomerChangeType.UPDATED
                )
            )

    for customer_id, customer in existing.items():
        if customer_id not in tripletex_ids and not customer.delete_flag:
            customer.delete_flag = True
            db.add(
                CustomerSyncLog(
                    customer_id=customer_id, change_type=CustomerChangeType.DELETED
                )
            )

    db.commit()
