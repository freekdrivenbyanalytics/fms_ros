"""Local-first create behavior for Customer/Product/CustomerLocation: these
route handlers touch a real DB session directly (app.main.create_customer
et al. are called as plain Python functions here, bypassing the HTTP
layer, matching this project's existing test style), so each test creates
real rows against the dev database and deletes them again in a `finally`
block - there is no isolated test database configured for this project."""
from unittest.mock import MagicMock, patch

from app.database import SessionLocal
from app.main import (
    _sync_warning,
    create_customer,
    create_customer_location,
    create_product,
)
from app.models import Customer, CustomerLocation, Product
from app.schemas import CustomerCreate, CustomerLocationCreate, ProductCreate, CustomerRescoSyncResult, CustomerLocationRescoSyncResult


def test_sync_warning_is_none_when_nothing_failed() -> None:
    assert _sync_warning([]) is None


def test_sync_warning_names_the_single_failed_system() -> None:
    assert "Tripletex" in _sync_warning(["Tripletex"])
    assert "Resco" not in _sync_warning(["Tripletex"])


def test_sync_warning_names_both_failed_systems() -> None:
    warning = _sync_warning(["Tripletex", "Resco"])
    assert "Tripletex" in warning
    assert "Resco" in warning


def test_create_customer_succeeds_locally_when_tripletex_and_resco_both_fail() -> None:
    db = SessionLocal()
    customer = None
    try:
        mock_client = MagicMock()
        mock_client.create_customer.side_effect = RuntimeError("Tripletex unreachable")
        with (
            patch("app.main._tripletex_client", return_value=mock_client),
            patch("app.main.sync_customer", side_effect=RuntimeError("Resco unreachable")),
        ):
            customer = create_customer(CustomerCreate(name="Test Co (local-first)"), db)

        assert customer.id is not None
        assert customer.tripletex_id is None
        assert "Tripletex" in customer.sync_warning
        assert "Resco" in customer.sync_warning
        assert db.get(Customer, customer.id) is not None
    finally:
        if customer is not None:
            db.delete(db.get(Customer, customer.id))
            db.commit()
        db.close()


def test_create_customer_has_no_warning_when_both_pushes_succeed() -> None:
    db = SessionLocal()
    customer = None
    try:
        mock_client = MagicMock()
        mock_client.create_customer.return_value = {"id": 5551234}
        with (
            patch("app.main._tripletex_client", return_value=mock_client),
            patch("app.main.sync_customer", return_value=CustomerRescoSyncResult(status="synced")),
        ):
            customer = create_customer(CustomerCreate(name="Test Co (synced)"), db)

        assert customer.tripletex_id == 5551234
        assert customer.sync_warning is None
    finally:
        if customer is not None:
            db.delete(db.get(Customer, customer.id))
            db.commit()
        db.close()


def test_create_product_succeeds_locally_when_tripletex_and_resco_both_fail() -> None:
    db = SessionLocal()
    product = None
    try:
        mock_client = MagicMock()
        mock_client.create_product.side_effect = RuntimeError("Tripletex unreachable")
        with (
            patch("app.main._tripletex_client", return_value=mock_client),
            patch("app.main.sync_product", side_effect=RuntimeError("Resco unreachable")),
        ):
            product = create_product(
                ProductCreate(product_type="TJN", number="99999", name="Test Product"), db
            )

        assert product.id is not None
        assert product.tripletex_id is None
        assert "Tripletex" in product.sync_warning
        assert "Resco" in product.sync_warning
    finally:
        if product is not None:
            db.delete(db.get(Product, product.id))
            db.commit()
        db.close()


def test_create_customer_location_succeeds_locally_when_tripletex_and_resco_both_fail() -> None:
    db = SessionLocal()
    customer = Customer(name="Test Co (for location)")
    db.add(customer)
    db.commit()
    db.refresh(customer)
    # This customer already has a tripletex_id, so the location create
    # attempts the Tripletex push (and it fails) rather than skipping it
    # for lack of a synced customer - a different code path, covered next.
    customer.tripletex_id = 42
    db.commit()

    location = None
    try:
        mock_client = MagicMock()
        mock_client.create_delivery_address.side_effect = RuntimeError("Tripletex unreachable")
        with (
            patch("app.main._tripletex_client", return_value=mock_client),
            patch("app.main.sync_customer_location", side_effect=RuntimeError("Resco unreachable")),
            patch("app.main.geocode_address", return_value=None),
        ):
            location = create_customer_location(
                CustomerLocationCreate(customer_id=customer.id, address_line_1="Test Street 1"),
                db,
            )

        assert location.id is not None
        assert location.tripletex_id is None
        assert "Tripletex" in location.sync_warning
        assert "Resco" in location.sync_warning
    finally:
        if location is not None:
            db.delete(db.get(CustomerLocation, location.id))
            db.commit()
        db.delete(db.get(Customer, customer.id))
        db.commit()
        db.close()


def test_create_customer_location_skips_tripletex_push_when_customer_not_synced() -> None:
    db = SessionLocal()
    customer = Customer(name="Test Co (unsynced)")
    db.add(customer)
    db.commit()
    db.refresh(customer)
    assert customer.tripletex_id is None

    location = None
    try:
        mock_client = MagicMock()
        with (
            patch("app.main._tripletex_client", return_value=mock_client),
            patch("app.main.sync_customer_location", return_value=CustomerLocationRescoSyncResult(status="synced")),
            patch("app.main.geocode_address", return_value=None),
        ):
            location = create_customer_location(
                CustomerLocationCreate(customer_id=customer.id, address_line_1="Test Street 2"),
                db,
            )

        mock_client.create_delivery_address.assert_not_called()
        assert location.tripletex_id is None
        assert "Tripletex" in location.sync_warning
    finally:
        if location is not None:
            db.delete(db.get(CustomerLocation, location.id))
            db.commit()
        db.delete(db.get(Customer, customer.id))
        db.commit()
        db.close()
