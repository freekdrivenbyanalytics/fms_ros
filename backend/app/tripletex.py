from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Customer,
    CustomerChangeType,
    CustomerLocation,
    CustomerLocationChangeType,
    CustomerLocationSyncLog,
    CustomerSyncLog,
    Product,
    ProductChangeType,
    ProductSyncLog,
)
from app.resco import (
    sync_customer_locations_to_resco,
    sync_customers_to_resco,
    sync_products_to_resco,
)

logger = logging.getLogger(__name__)

# Only products whose number starts with one of these prefixes are synced;
# see sync_products. "TJN" = tjeneste/service, "PRD" = produkt/product.
PRODUCT_NUMBER_PREFIXES = ("TJN", "PRD")

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

    def get_delivery_addresses(self) -> list[dict]:
        page_size = 100
        offset = 0
        addresses: list[dict] = []
        fields = (
            "id,version,url,addressLine1,addressLine2,postalCode,city,country,"
            "addressAsString,displayName,name,customerVendor(id)"
        )

        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            while True:
                response = client.get(
                    f"{self._base_url}/deliveryAddress",
                    auth=self._auth(),
                    params={"from": offset, "count": page_size, "fields": fields},
                )
                if response.status_code >= 400:
                    raise TripletexAuthError(
                        f"Tripletex delivery address fetch failed: {response.status_code} {response.text}"
                    )
                body = response.json()
                page = body["values"]
                addresses.extend(page)
                if len(page) < page_size or len(addresses) >= body["fullResultSize"]:
                    break
                offset += page_size

        return addresses

    def get_products(self) -> list[dict]:
        page_size = 100
        offset = 0
        products: list[dict] = []

        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            while True:
                response = client.get(
                    f"{self._base_url}/product",
                    auth=self._auth(),
                    params={"from": offset, "count": page_size},
                )
                if response.status_code >= 400:
                    raise TripletexAuthError(
                        f"Tripletex product fetch failed: {response.status_code} {response.text}"
                    )
                body = response.json()
                page = body["values"]
                products.extend(page)
                if len(page) < page_size or len(products) >= body["fullResultSize"]:
                    break
                offset += page_size

        # Tripletex's /product `number` query param expects a comma-separated
        # list of numeric ids, not a substring filter (confirmed against the
        # live API — it 422s on a non-numeric value), so the prefix filter is
        # applied client-side instead.
        return [
            p
            for p in products
            if (p.get("number") or "").startswith(PRODUCT_NUMBER_PREFIXES)
        ]

    def create_customer(self, data: dict) -> dict:
        """Create a customer. Tripletex has no standalone create endpoint for
        a delivery address (/deliveryAddress only supports GET/PUT) — a
        customer's delivery address is created as a side effect of this call
        by including a `deliveryAddress` object in `data`; the response's
        `deliveryAddress.id` is that address's Tripletex id."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/customer",
                auth=self._auth(),
                json=data,
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex customer create failed: {response.status_code} {response.text}"
            )
        return response.json()["value"]

    def update_customer(self, customer_id: int, data: dict) -> dict:
        """Update a customer's own fields (name, email, phone, organization
        number, etc.) — not the same as adding a customer location; see
        `create_delivery_address`/`update_delivery_address` for that."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.put(
                f"{self._base_url}/customer/{customer_id}",
                auth=self._auth(),
                json=data,
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex customer update failed: {response.status_code} {response.text}"
            )
        return response.json()["value"]

    def delete_customer(self, customer_id: int) -> None:
        """Delete a customer. Tripletex has no standalone delete endpoint for
        a delivery address (/deliveryAddress/{id} only supports GET/PUT) —
        deleting the owning customer cascades away its delivery address."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.delete(
                f"{self._base_url}/customer/{customer_id}",
                auth=self._auth(),
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex customer delete failed: {response.status_code} {response.text}"
            )

    def create_delivery_address(self, customer_id: int, data: dict) -> dict:
        """Add a new delivery address (customer location) to an existing
        customer. Confirmed live: a customer-level PUT with a nested
        `deliveryAddress` object creates a genuinely new, independent
        delivery address every call (it does not update any existing one) —
        see openspec/changes/add-master-data-crud/design.md."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.put(
                f"{self._base_url}/customer/{customer_id}",
                auth=self._auth(),
                json={"deliveryAddress": data},
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex delivery address create failed: {response.status_code} {response.text}"
            )
        return response.json()["value"]["deliveryAddress"]

    def update_delivery_address(self, location_id: int, data: dict) -> dict:
        """Update an existing delivery address (customer location) in place."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.put(
                f"{self._base_url}/deliveryAddress/{location_id}",
                auth=self._auth(),
                json=data,
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex delivery address update failed: {response.status_code} {response.text}"
            )
        return response.json()["value"]

    def create_product(self, data: dict) -> dict:
        """Create a product. Confirmed live: `number`/`name` alone is
        sufficient — Tripletex fills in every other field with defaults."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(
                f"{self._base_url}/product",
                auth=self._auth(),
                json=data,
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex product create failed: {response.status_code} {response.text}"
            )
        return response.json()["value"]

    def update_product(self, product_id: int, data: dict) -> dict:
        """Update a product's fields."""
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.put(
                f"{self._base_url}/product/{product_id}",
                auth=self._auth(),
                json=data,
            )
        if response.status_code >= 400:
            raise TripletexAuthError(
                f"Tripletex product update failed: {response.status_code} {response.text}"
            )
        return response.json()["value"]


def _customer_push_payload(customer: Customer) -> dict:
    """The subset of a customer's fields fms_ros actually edits and pushes
    outward - matches what create_customer/update_customer already send,
    not a full reconstruction of every Tripletex field (most of Customer's
    other columns were only ever populated by the old pull sync, which no
    longer exists)."""
    return {
        "name": customer.name,
        "email": customer.email,
        "phoneNumber": customer.phone_number,
        "organizationNumber": customer.organization_number,
    }


def sync_customers(db: Session) -> dict[str, int]:
    """Bootstrap-push every non-deleted, non-archived customer to Tripletex
    and Resco: create upstream whatever has no remembered tripletex_id,
    update upstream whatever already does. Runs on demand only - see
    local-first-masterdata-sync's design.md. Must complete before
    sync_customer_locations runs in the same bootstrap-sync call, since a
    location's Tripletex push needs its customer's tripletex_id.
    """
    client = TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)
    customers = (
        db.query(Customer)
        .filter(Customer.delete_flag.is_(False), Customer.archived.is_(False))
        .all()
    )

    created = updated = failed = 0
    for customer in customers:
        payload = _customer_push_payload(customer)
        try:
            if customer.tripletex_id is None:
                data = client.create_customer(payload)
                customer.tripletex_id = data["id"]
                db.add(
                    CustomerSyncLog(
                        customer_id=customer.id, change_type=CustomerChangeType.CREATED
                    )
                )
                created += 1
            else:
                client.update_customer(customer.tripletex_id, payload)
                db.add(
                    CustomerSyncLog(
                        customer_id=customer.id, change_type=CustomerChangeType.UPDATED
                    )
                )
                updated += 1
        except Exception:
            logger.warning("Tripletex bootstrap push failed for customer %s", customer.id, exc_info=True)
            failed += 1

    db.commit()

    try:
        sync_customers_to_resco(db)
    except Exception:
        logger.warning("Resco customer sync failed after bootstrap sync", exc_info=True)

    return {"created": created, "updated": updated, "failed": failed}


def _location_push_payload(location: CustomerLocation) -> dict:
    return {
        "addressLine1": location.address_line_1,
        "addressLine2": location.address_line_2,
        "postalCode": location.postal_code,
        "city": location.city,
    }


def sync_customer_locations(db: Session) -> dict[str, int]:
    """Bootstrap-push every non-deleted, non-archived customer location to
    Tripletex and Resco. Must run after sync_customers in the same
    bootstrap-sync call: a location whose customer has no tripletex_id yet
    (even one created moments ago by this same run) is skipped rather than
    pushed - see local-first-masterdata-sync's design.md ("push customers
    before their locations").
    """
    client = TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)
    locations = (
        db.query(CustomerLocation)
        .filter(CustomerLocation.delete_flag.is_(False), CustomerLocation.archived.is_(False))
        .all()
    )

    created = updated = skipped = failed = 0
    for location in locations:
        customer = location.customer
        if customer.tripletex_id is None:
            skipped += 1
            continue

        payload = _location_push_payload(location)
        try:
            if location.tripletex_id is None:
                data = client.create_delivery_address(customer.tripletex_id, payload)
                location.tripletex_id = data["id"]
                db.add(
                    CustomerLocationSyncLog(
                        customer_location_id=location.id,
                        change_type=CustomerLocationChangeType.CREATED,
                    )
                )
                created += 1
            else:
                client.update_delivery_address(location.tripletex_id, payload)
                db.add(
                    CustomerLocationSyncLog(
                        customer_location_id=location.id,
                        change_type=CustomerLocationChangeType.UPDATED,
                    )
                )
                updated += 1
        except Exception:
            logger.warning(
                "Tripletex bootstrap push failed for customer location %s", location.id, exc_info=True
            )
            failed += 1

    db.commit()

    try:
        sync_customer_locations_to_resco(db)
    except Exception:
        logger.warning(
            "Resco customer location sync failed after bootstrap sync", exc_info=True
        )

    return {"created": created, "updated": updated, "skipped": skipped, "failed": failed}


def _product_push_payload(product: Product) -> dict:
    return {"number": product.number, "name": product.name}


def sync_products(db: Session) -> dict[str, int]:
    """Bootstrap-push every non-deleted, non-archived product to Tripletex
    and Resco. Runs on demand only - see local-first-masterdata-sync's
    design.md."""
    client = TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)
    products = (
        db.query(Product)
        .filter(Product.delete_flag.is_(False), Product.archived.is_(False))
        .all()
    )

    created = updated = failed = 0
    for product in products:
        payload = _product_push_payload(product)
        try:
            if product.tripletex_id is None:
                data = client.create_product(payload)
                product.tripletex_id = data["id"]
                db.add(
                    ProductSyncLog(
                        product_id=product.id, change_type=ProductChangeType.CREATED
                    )
                )
                created += 1
            else:
                client.update_product(product.tripletex_id, payload)
                db.add(
                    ProductSyncLog(
                        product_id=product.id, change_type=ProductChangeType.UPDATED
                    )
                )
                updated += 1
        except Exception:
            logger.warning("Tripletex bootstrap push failed for product %s", product.id, exc_info=True)
            failed += 1

    db.commit()

    try:
        sync_products_to_resco(db)
    except Exception:
        logger.warning("Resco product sync failed after bootstrap sync", exc_info=True)

    return {"created": created, "updated": updated, "failed": failed}
