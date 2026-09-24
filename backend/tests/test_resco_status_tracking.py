from datetime import datetime, timedelta
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

import pytest

from app import resco
from app.main import _assign_visit
from app.models import VisitStatus
from app.schemas import RescoStatusSyncSummary
from scripts.seed_demo_contacts import fill_missing_contacts


def location(**changes):
    fields = dict(address="Street 1", address_line_1="Street 1", address_line_2=None,
                  postal_code="0123", city="Oslo", country={"name": "Norway"},
                  latitude=59.9, longitude=10.7, resco_functional_location_id=None,
                  resco_asset_id=None, customer=NS(name="Customer", resco_account_id="account"))
    return NS(**(fields | changes))


def assignment(visit_id=1, **changes):
    fields = dict(service_visit_id=visit_id, resco_work_order_id="work-order",
                  resco_work_order_schedule_id=None, resco_status=None, resco_statecode=None,
                  resco_statuscode=None, planned_start=datetime.now() - timedelta(days=1),
                  planned_end=datetime.now(), pinned=True, employee=NS(resco_user_id="user"),
                  service_visit=NS(contract_line=NS(customer_location=location(
                      resco_asset_id="asset", resco_functional_location_id="location"))))
    return NS(**(fields | changes))


def test_location_retry_keeps_successful_functional_location(monkeypatch):
    client = MagicMock()
    client.create_functional_location.return_value = {"id": "functional"}
    client.create_asset.side_effect = [RuntimeError("offline"), {"id": "asset"}]
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    db, loc = MagicMock(), location()
    assert resco.sync_customer_location(db, loc).status == "failed"
    assert loc.resco_functional_location_id == "functional"
    assert loc.resco_asset_id is None
    assert resco.sync_customer_location(db, loc).status == "synced"
    client.create_functional_location.assert_called_once()
    assert loc.resco_asset_id == "asset"


def test_location_payloads_keep_distinct_coordinates_and_equal_names():
    first = location(resco_functional_location_id="first")
    second = location(latitude=60.1, resco_functional_location_id="second")
    assert resco.RescoClient._functional_location_payload(first)["resco_latitude"] == 59.9
    assert resco.RescoClient._functional_location_payload(second)["resco_latitude"] == 60.1
    for loc in (first, second):
        assert resco.RescoClient._asset_payload(loc)["name"] == resco.RescoClient._functional_location_payload(loc)["name"]
        assert loc.resco_functional_location_id in resco.RescoClient._asset_payload(loc)["resco_functionallocationid_resco_functionallocation@odata.bind"]
    no_coords = location(latitude=None, longitude=None)
    assert "resco_latitude" not in resco.RescoClient._functional_location_payload(no_coords)
    no_coords.latitude, no_coords.longitude = 1.0, 2.0
    assert resco.RescoClient._functional_location_payload(no_coords)["resco_longitude"] == 2.0


def test_work_order_retry_keeps_parent_and_does_not_reset_status(monkeypatch):
    client = MagicMock()
    client.create_work_order.return_value = {"id": "parent"}
    client.create_work_order_schedule.side_effect = [RuntimeError("offline"), {"id": "child"}]
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    item = assignment(resco_work_order_id=None)
    db = MagicMock()
    assert resco.sync_assignment(db, item).status == "failed"
    assert item.resco_work_order_id == "parent"
    assert resco.sync_assignment(db, item).status == "synced"
    client.create_work_order.assert_called_once()
    client.update_work_order.assert_called_once()
    assert item.resco_work_order_schedule_id == "child"


def test_work_order_names_remain_unique_with_long_addresses():
    first, second = assignment(1), assignment(2)
    for item in (first, second):
        item.service_visit.contract_line.customer_location.address = "a" * 200
    p1, p2 = (resco.RescoClient._work_order_payload(item) for item in (first, second))
    assert len(p1["name"]) == 160
    assert p1["name"] != p2["name"]
    assert p1["name"].endswith("Visit 1")
    assert "statuscode" not in p1
    assert p1["customerid_account@odata.bind"] == "/account(account)"


def test_status_pull_continues_after_failure_and_unassigns_past_scheduled(monkeypatch):
    items = [assignment(1), assignment(2), assignment(3), assignment(4, resco_work_order_id=None)]
    client = MagicMock()
    client.get_work_order_status.side_effect = [RuntimeError("offline"),
        {"statecode": 0, "statuscode": 5, "statuscode@RescoCloud.FormattedValue": "Scheduled"},
        {"statecode": 1, "statuscode": 2, "statuscode@RescoCloud.FormattedValue": "Closed"}]
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    db = MagicMock()
    db.query.return_value.all.return_value = items
    summary = resco.sync_assignment_statuses_from_resco(db)
    assert (summary.pulled, summary.failed, summary.skipped) == (2, 1, 1)
    assert summary.reconciled == 1
    assert items[1].resco_status == "Scheduled" and items[2].resco_status == "Closed"
    db.delete.assert_called_once_with(items[1])
    assert items[1].service_visit.status == VisitStatus.UNASSIGNED
    assert not items[1].pinned


@pytest.mark.parametrize("statecode,completed", [(None, False), (0, False), (1, True), (2, False)])
def test_completed_uses_raw_state(statecode, completed):
    assert resco._is_resco_status_completed(statecode) == completed


def test_assignment_clears_reason():
    visit = NS(id=10, status=VisitStatus.UNASSIGNED, unassigned_reason="Missed",
               contract_line=NS(duration_minutes=30))
    _assign_visit(MagicMock(), visit, NS(id=3), datetime.now())
    assert visit.unassigned_reason is None
    assert visit.status == VisitStatus.ASSIGNED


def test_contact_payload_explicitly_clears_values():
    customer = NS(contact_name=None, email=None, phone_number=None,
                  phone_number_mobile=None, resco_account_id="account")
    payload = resco.RescoClient._contact_payload(customer)
    assert payload["lastname"] is None
    assert payload["mobilephone"] is None
    assert payload["parentcustomerid_account@odata.bind"] == "/account(account)"


def test_demo_seed_preserves_existing_values_and_is_repeatable():
    customer = NS(contact_name=None, email="existing@example.invalid", phone_number=None,
                  phone_number_mobile=None)
    assert fill_missing_contacts(customer, "demo")
    assert customer.email == "existing@example.invalid"
    assert not fill_missing_contacts(customer, "demo")


def test_updating_unresolved_coordinates_clears_stale_remote_coordinates(monkeypatch):
    client = resco.RescoClient("https://example.invalid", "", "")
    request = MagicMock(return_value={})
    monkeypatch.setattr(client, "_request", request)
    client.update_functional_location(location(latitude=None, longitude=None,
                                               resco_functional_location_id="functional"))
    payload = request.call_args.kwargs["json"]
    assert payload["resco_latitude"] is None and payload["resco_longitude"] is None


def test_customer_contact_retry_reuses_ids_and_propagates_changes(monkeypatch):
    client_type = resco.RescoClient
    client = MagicMock()
    client.create_account.return_value = {"id": "shared-account"}
    client.create_contact.return_value = {"id": "contact"}
    client.link_contact.side_effect = [RuntimeError("offline"), None, None]
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    customer = NS(name="Original", contact_name="Person", email="old@example.invalid",
                  phone_number="123", phone_number_mobile="456", organization_number=None,
                  resco_account_id=None, resco_contact_id=None, locations=[])
    first = location(customer=customer, resco_functional_location_id="first", resco_asset_id="asset1")
    second = location(customer=customer, resco_functional_location_id="second", resco_asset_id="asset2",
                      latitude=60.1, longitude=11.2)
    customer.locations = [first, second]
    db = MagicMock()
    assert resco.sync_customer(db, customer).status == "failed"
    assert (customer.resco_account_id, customer.resco_contact_id) == ("shared-account", "contact")
    customer.name, customer.contact_name = "Renamed", "New person"
    assert resco.sync_customer(db, customer).status == "synced"
    assert client_type._contact_payload(customer)["lastname"] == "New person"
    customer.contact_name = customer.email = customer.phone_number = customer.phone_number_mobile = None
    assert resco.sync_customer(db, customer).status == "synced"
    payload = client_type._contact_payload(customer)
    assert all(payload[key] is None for key in ("lastname", "emailaddress1", "telephone1", "mobilephone"))
    client.create_account.assert_called_once()
    client.create_contact.assert_called_once()
    assert client.update_contact.call_count == 2
    for loc, functional, asset in ((first, "first", "asset1"), (second, "second", "asset2")):
        assert resco.sync_customer_location(db, loc).status == "synced"
        assert (loc.resco_functional_location_id, loc.resco_asset_id) == (functional, asset)
        assert client_type._asset_payload(loc)["customerid_account@odata.bind"] == "/account(shared-account)"
    assert (first.latitude, second.latitude) == (59.9, 60.1)
    client.create_asset.assert_not_called()
    client.create_functional_location.assert_not_called()


def test_existing_asset_catchup_and_duplicate_location_names_reuse_identity(monkeypatch):
    client = MagicMock()
    client.create_functional_location.side_effect = [{"id": "first"}, {"id": "second"}]
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    first, second = location(resco_asset_id="asset1"), location(resco_asset_id="asset2")
    for loc in (first, second):
        assert resco.sync_customer_location(MagicMock(), loc).status == "synced"
        assert resco.sync_customer_location(MagicMock(), loc).status == "synced"
    assert first.resco_functional_location_id != second.resco_functional_location_id
    assert client.create_functional_location.call_count == 2
    assert client.update_asset.call_count == 4
    client.create_asset.assert_not_called()


def test_location_bulk_sync_excludes_deleted_locations_and_parents(monkeypatch):
    from app.database import SessionLocal
    from app.models import Customer, CustomerLocation
    from app.schemas import CustomerLocationRescoSyncResult

    synced = []
    def capture(db, loc):
        synced.append(loc.id)
        return CustomerLocationRescoSyncResult(status="synced")

    monkeypatch.setattr(resco, "sync_customer_location", capture)
    with SessionLocal() as db:
        try:
            parents = [Customer(name="Resco filter test", **flags) for flags in
                       ({}, {"delete_flag": True}, {"archived": True})]
            db.add_all(parents)
            db.flush()
            locations = [CustomerLocation(customer=parent, address="Test", **flags)
                         for parent, flags in ((parents[0], {}), (parents[0], {"delete_flag": True}),
                                               (parents[0], {"archived": True}), (parents[1], {}),
                                               (parents[2], {}))]
            db.add_all(locations)
            db.flush()
            resco.sync_customer_locations_to_resco(db)
            assert locations[0].id in synced
            assert all(loc.id not in synced for loc in locations[1:])
        finally:
            db.rollback()


@pytest.mark.parametrize("days,state,status,expected", [
    (-1, 0, 5, 1), (0, 0, 5, 0), (1, 0, 5, 0),
    (-1, 1, 2, 0), (-1, 0, 1, 0), (-1, 0, 3, 0),
])
def test_reconciliation_uses_planned_day_and_current_status(monkeypatch, days, state, status, expected):
    item = assignment(planned_start=datetime.now() + timedelta(days=days))
    item.service_visit.requested_date = (datetime.now() - timedelta(days=30)).date()
    # A previously completed observation does not disqualify current Scheduled status.
    item.resco_statecode, item.resco_statuscode = 1, 2
    client = MagicMock()
    client.get_work_order_status.return_value = {"statecode": state, "statuscode": status}
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    db = MagicMock()
    db.query.return_value.all.return_value = [item]
    summary = resco.sync_assignment_statuses_from_resco(db)
    assert summary.reconciled == expected
    assert db.delete.call_count == expected
    if expected:
        reset = db.add.call_args.args[0]
        assert reset.work_order_id == "work-order"
        assert reset.service_visit_id == item.service_visit_id
        assert item.service_visit.unassigned_reason


def test_draft_reset_failure_is_retryable_without_assignment():
    reset = NS(work_order_id="old-order", service_visit_id=1, status="pending", last_error=None)
    db, client = MagicMock(), MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [reset]
    db.query.return_value.filter.return_value.first.return_value = None
    client.get_work_order_status.return_value = {"statecode": 0, "statuscode": 5, "@odata.etag": 'W/"version"'}
    client._request.side_effect = [RuntimeError("offline"), {}]
    first = RescoStatusSyncSummary()
    resco._retry_draft_resets(db, client, first)
    assert first.reset_failed == 1 and reset.status == "pending"
    assert reset.last_error == "offline"
    second = RescoStatusSyncSummary()
    resco._retry_draft_resets(db, client, second)
    assert second.reset_failed == 0 and reset.status == "completed"
    assert reset.last_error is None
    assert client._request.call_args.kwargs["headers"] == {"If-Match": 'W/"version"'}


@pytest.mark.parametrize("codes,active_assignment,result", [
    ((1, 2), None, "cancelled"), ((0, 3), None, "cancelled"),
    ((0, 5), object(), "cancelled"), ((0, 1), None, "completed"),
])
def test_reset_retry_does_not_overwrite_progress_or_reassigned_order(codes, active_assignment, result):
    reset = NS(work_order_id="old-order", service_visit_id=1, status="pending", last_error="offline")
    db, client = MagicMock(), MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [reset]
    db.query.return_value.filter.return_value.first.return_value = active_assignment
    client.get_work_order_status.return_value = dict(zip(("statecode", "statuscode"), codes))
    resco._retry_draft_resets(db, client, RescoStatusSyncSummary())
    assert reset.status == result
    client._request.assert_not_called()


def test_reset_without_version_defers_remote_write():
    reset = NS(work_order_id="old-order", service_visit_id=1, status="pending", last_error=None)
    db, client = MagicMock(), MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [reset]
    db.query.return_value.filter.return_value.first.return_value = None
    client.get_work_order_status.return_value = {"statecode": 0, "statuscode": 5}
    summary = RescoStatusSyncSummary()
    resco._retry_draft_resets(db, client, summary)
    assert reset.status == "pending" and summary.reset_failed == 1
    client._request.assert_not_called()


def test_local_unassignment_and_retry_context_survive_remote_failure(monkeypatch):
    from sqlalchemy.orm import Session
    from app.database import engine
    from app.models import Assignment, ContractLine, Employee, RescoDraftReset, ServiceVisit

    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            line, employee = db.query(ContractLine).first(), db.query(Employee).first()
            if not line or not employee:
                pytest.skip("Needs a development contract line and employee")
            visit = ServiceVisit(contract_line_id=line.id,
                                 requested_date=(datetime.now() + timedelta(days=10)).date(),
                                 status=VisitStatus.ASSIGNED)
            db.add(visit)
            db.flush()
            item = Assignment(service_visit_id=visit.id, employee_id=employee.id,
                              planned_start=datetime.now() - timedelta(days=1),
                              planned_end=datetime.now(), pinned=True,
                              resco_work_order_id="test-durable-reset", resco_work_order_schedule_id="schedule")
            db.add(item)
            db.commit()
            visit_id = visit.id
            original_query = db.query
            def scoped_query(model):
                query = original_query(model)
                if model is Assignment:
                    return query.filter(Assignment.service_visit_id == visit_id)
                if model is RescoDraftReset:
                    return query.filter(RescoDraftReset.work_order_id == "test-durable-reset")
                return query
            monkeypatch.setattr(db, "query", scoped_query)
            client = MagicMock()
            client.get_work_order_status.return_value = {"statecode": 0, "statuscode": 5, "@odata.etag": 'W/"1"'}
            client._request.side_effect = [RuntimeError("offline"), {}]
            monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
            summary = resco.sync_assignment_statuses_from_resco(db)
            assert summary.reconciled == 1 and summary.reset_failed == 1
            db.expire_all()
            assert db.get(Assignment, visit_id) is None
            assert db.get(ServiceVisit, visit_id).status == VisitStatus.UNASSIGNED
            assert db.get(ServiceVisit, visit_id).unassigned_reason
            reset = db.get(RescoDraftReset, "test-durable-reset")
            assert reset.status == "pending" and reset.schedule_id == "schedule"
            summary = resco.sync_assignment_statuses_from_resco(db)
            assert summary.reconciled == 0 and summary.reset_failed == 0
            db.expire_all()
            assert db.get(RescoDraftReset, "test-durable-reset").status == "completed"
        finally:
            db.close()
            transaction.rollback()
