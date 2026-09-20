"""The new push-based bootstrap-sync functions in app.tripletex. Real DB
rows (no isolated test database configured for this project - see
test_masterdata_local_first_sync.py), deleted in a `finally` block.

Known trade-off: sync_customers/sync_customer_locations/sync_products each
process every non-deleted, non-archived row in their table, not just the
ones a test creates - so running them here also logs a harmless
CustomerSyncLog/CustomerLocationSyncLog/ProductSyncLog "updated" entry for
every other real, already-synced row in the dev DB (their tripletex_id is
unaffected - only the log table gains noise). Accepted as a known,
low-stakes side effect of testing against this project's shared dev
database rather than an isolated test database, which doesn't exist here.
"""
from unittest.mock import MagicMock, patch

from app.database import SessionLocal
from app.models import (
    Customer,
    CustomerLocation,
    CustomerLocationSyncLog,
    CustomerSyncLog,
    Product,
    ProductSyncLog,
)
from app.tripletex import sync_customer_locations, sync_customers, sync_products


def _delete_customer(db, customer_id: int) -> None:
    db.query(CustomerSyncLog).filter(CustomerSyncLog.customer_id == customer_id).delete()
    db.delete(db.get(Customer, customer_id))


def _delete_location(db, location_id: int) -> None:
    db.query(CustomerLocationSyncLog).filter(
        CustomerLocationSyncLog.customer_location_id == location_id
    ).delete()
    db.delete(db.get(CustomerLocation, location_id))


def _delete_product(db, product_id: int) -> None:
    db.query(ProductSyncLog).filter(ProductSyncLog.product_id == product_id).delete()
    db.delete(db.get(Product, product_id))


def test_sync_customers_creates_missing_and_updates_present() -> None:
    db = SessionLocal()
    unsynced = Customer(name="Bootstrap Test - unsynced")
    synced = Customer(name="Bootstrap Test - synced", tripletex_id=777001)
    db.add_all([unsynced, synced])
    db.commit()
    db.refresh(unsynced)
    db.refresh(synced)

    try:
        mock_client = MagicMock()
        mock_client.create_customer.return_value = {"id": 777002}
        with (
            patch("app.tripletex.TripletexClient", return_value=mock_client),
            patch("app.tripletex.sync_customers_to_resco", return_value=None),
        ):
            summary = sync_customers(db)

        db.refresh(unsynced)
        assert unsynced.tripletex_id == 777002
        # The dev DB has other, already-synced customers too (every
        # pre-existing row got tripletex_id backfilled by the migration),
        # so this only asserts our own two rows were each handled the
        # expected way - not exact call counts across the whole table.
        assert any(
            call.args[0] == 777001 for call in mock_client.update_customer.call_args_list
        )
        assert summary["created"] >= 1
        assert summary["updated"] >= 1
    finally:
        _delete_customer(db, unsynced.id)
        _delete_customer(db, synced.id)
        db.commit()
        db.close()


def test_sync_customers_one_failure_does_not_block_the_rest() -> None:
    db = SessionLocal()
    ok = Customer(name="Bootstrap Test - ok")
    fails = Customer(name="Bootstrap Test - fails")
    db.add_all([ok, fails])
    db.commit()
    db.refresh(ok)
    db.refresh(fails)

    try:
        mock_client = MagicMock()

        def create_side_effect(payload):
            if payload["name"] == fails.name:
                raise RuntimeError("Tripletex error")
            return {"id": 777003}

        mock_client.create_customer.side_effect = create_side_effect
        with (
            patch("app.tripletex.TripletexClient", return_value=mock_client),
            patch("app.tripletex.sync_customers_to_resco", return_value=None),
        ):
            summary = sync_customers(db)

        db.refresh(ok)
        db.refresh(fails)
        assert ok.tripletex_id == 777003
        assert fails.tripletex_id is None
        assert summary["failed"] >= 1
        assert summary["created"] >= 1
    finally:
        _delete_customer(db, ok.id)
        _delete_customer(db, fails.id)
        db.commit()
        db.close()


def test_sync_customer_locations_skips_unsynced_customer_and_picks_up_synced_one() -> None:
    db = SessionLocal()
    unsynced_customer = Customer(name="Bootstrap Test - loc parent unsynced")
    # Already synced (e.g. by an earlier sync_customers call, or by its own
    # create push) - directly assigned rather than routed through
    # sync_customers(db) here, since that call would process every other
    # real, already-synced customer in the dev DB too and isn't the thing
    # this test is checking (see
    # test_sync_customers_creates_missing_and_updates_present for that).
    fresh_customer = Customer(name="Bootstrap Test - loc parent fresh", tripletex_id=777004)
    db.add_all([unsynced_customer, fresh_customer])
    db.commit()
    db.refresh(unsynced_customer)
    db.refresh(fresh_customer)

    still_skipped_location = CustomerLocation(
        customer_id=unsynced_customer.id, address_line_1="Skip St 1", address="Skip St 1"
    )
    picked_up_location = CustomerLocation(
        customer_id=fresh_customer.id, address_line_1="Pickup St 1", address="Pickup St 1"
    )
    db.add_all([still_skipped_location, picked_up_location])
    db.commit()
    db.refresh(still_skipped_location)
    db.refresh(picked_up_location)

    try:
        mock_client = MagicMock()
        mock_client.create_delivery_address.return_value = {"id": 888001}
        with (
            patch("app.tripletex.TripletexClient", return_value=mock_client),
            patch("app.tripletex.sync_customer_locations_to_resco", return_value=None),
        ):
            summary = sync_customer_locations(db)

        db.refresh(still_skipped_location)
        db.refresh(picked_up_location)
        assert still_skipped_location.tripletex_id is None
        assert picked_up_location.tripletex_id == 888001
        assert summary["skipped"] >= 1
        assert any(
            call.args[0] == 777004
            for call in mock_client.create_delivery_address.call_args_list
        )
    finally:
        _delete_location(db, still_skipped_location.id)
        _delete_location(db, picked_up_location.id)
        _delete_customer(db, unsynced_customer.id)
        _delete_customer(db, fresh_customer.id)
        db.commit()
        db.close()


def test_sync_products_creates_missing_and_updates_present() -> None:
    db = SessionLocal()
    unsynced = Product(number="TJN99991", name="Bootstrap Test Product - unsynced")
    synced = Product(number="TJN99992", name="Bootstrap Test Product - synced", tripletex_id=777005)
    db.add_all([unsynced, synced])
    db.commit()
    db.refresh(unsynced)
    db.refresh(synced)

    try:
        mock_client = MagicMock()
        mock_client.create_product.return_value = {"id": 777006}
        with (
            patch("app.tripletex.TripletexClient", return_value=mock_client),
            patch("app.tripletex.sync_products_to_resco", return_value=None),
        ):
            summary = sync_products(db)

        db.refresh(unsynced)
        assert unsynced.tripletex_id == 777006
        assert any(
            call.args[0] == 777005 for call in mock_client.update_product.call_args_list
        )
        assert summary["created"] >= 1
        assert summary["updated"] >= 1
    finally:
        _delete_product(db, unsynced.id)
        _delete_product(db, synced.id)
        db.commit()
        db.close()
