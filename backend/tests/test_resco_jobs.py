from contextlib import nullcontext
from copy import deepcopy
from types import SimpleNamespace as NS
from uuid import uuid4
import re

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import main, resco, resco_jobs as jobs
from app.database import engine
from app.models import Product, RescoSyncRecord, ServiceOrderType, Task
from app.schemas import ProductCreate, ProductRescoSyncResult, ServiceOrderTypeCreate, ServiceOrderTypeUpdate, TaskInput


class Remote:
    def __init__(self):
        self.data = {}
        self.posts = []
        self.patches = []
        self.fail_entity = None
        self.lose_response = False

    def add(self, entity, **data):
        data.setdefault("id", str(uuid4()))
        data.setdefault("statecode", 0)
        data.setdefault("statuscode", 1)
        data["@odata.etag"] = "version"
        self.data.setdefault(entity, {})[data["id"]] = data
        return data

    def _request(self, method, path, **kwargs):
        entity = path.split("('")[0]
        rid = path.split("('")[1].split("')")[0] if "('" in path else None
        if method == "GET":
            if rid:
                return deepcopy(self.data[entity][rid])
            values = list(self.data.get(entity, {}).values())
            for field, raw in re.findall(r"(\w+) eq ('[^']*'|\d+)", kwargs.get("params", {}).get("$filter", "")):
                value = raw[1:-1] if raw.startswith("'") else int(raw)
                values = [v for v in values if v.get(field) == value]
            return {"value": deepcopy(values)}
        if entity == self.fail_entity:
            raise RuntimeError("offline")
        payload = deepcopy(kwargs["json"])
        converted = {}
        for key, value in payload.items():
            if key.endswith("@odata.bind"):
                target, identifier = value[1:-1].split("(", 1)
                lookup = key.removesuffix("@odata.bind").removesuffix("_" + target)
                converted["__" + lookup + "_id"] = identifier
            else:
                converted[key] = value
        if method == "POST":
            assert payload["id"] not in self.data.get(entity, {}), "duplicate POST"
            self.posts.append((entity, payload))
            result = self.add(entity, **converted)
            if self.lose_response:
                self.lose_response = False
                raise TimeoutError("response lost")
            return deepcopy(result)
        self.patches.append((entity, rid, payload))
        self.data[entity][rid].update(converted)
        return deepcopy(self.data[entity][rid])


@pytest.fixture
def db():
    # SAVEPOINT commits exercise production identity persistence without touching real rows.
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()


@pytest.fixture
def remote(monkeypatch):
    client = Remote()
    client.add("pricelevel", id="price", __transactioncurrencyid_id="nok")
    monkeypatch.setattr(jobs, "sync_lock", lambda db: nullcontext())
    monkeypatch.setattr(jobs, "client_for_resco", lambda: client)
    monkeypatch.setattr(jobs, "nok_setup", lambda *args, **kwargs: ("nok", "price"))
    monkeypatch.setattr(jobs, "sync_product", lambda db, product, **kwargs: ProductRescoSyncResult(status="synced"))
    return client


def catalog(db):
    one = main.create_task(TaskInput(name="Inspection", description="Inspect", estimated_duration_minutes=5), db)
    two = main.create_task(TaskInput(name="Snow"), db)
    a = ServiceOrderType(name="General")
    b = ServiceOrderType(name="Winter")
    db.add_all([a, b]); db.flush()
    main._task_links(db, a, [one.id])
    main._task_links(db, b, [one.id, two.id])
    db.commit()
    return one, two, a, b


def visit(db, remote):
    one, two, a, b = catalog(db)
    products = [NS(id=8001 + i, name=f"Product {i}", resco_product_id=f"p{i}",
                   delete_flag=False, archived=False, product_type="TJN", service_order_type=t,
                   service_order_type_id=t.id if t else None) for i, t in enumerate([a, a, b, None])]
    parent = remote.add("fs_workorder", statuscode=5)
    assignment = NS(resco_work_order_id=parent["id"], service_visit=NS(contract_line=NS(required_products=products)))
    return assignment, (one, two, a, b)


def test_shared_task_template_lifecycle_and_warnings(db, remote):
    one, two, a, b = catalog(db)
    assert jobs.sync_types(db, [a.id, b.id]).created == 2
    assert len(remote.data["fs_incidenttemplatetask"]) == 3
    first = a.task_links[0].resco_task_id
    main.update_service_order_type(a.id, ServiceOrderTypeUpdate(name="Renamed", task_ids=[]), db)
    assert remote.data["fs_incidenttemplatetask"][first]["statecode"] == 1
    main.update_service_order_type(a.id, ServiceOrderTypeUpdate(name="Renamed", task_ids=[one.id]), db)
    assert a.task_links[0].resco_task_id == first
    assert remote.data["fs_incidenttemplatetask"][first]["statecode"] == 0
    remote.fail_entity = "fs_incidenttemplatetask"
    result = main.update_task(one.id, TaskInput(name="Changed"), db)
    assert result.name == "Changed" and "offline" in result.sync_warning
    remote.fail_entity = None
    assert jobs.sync_types(db, [a.id, b.id]).failed == 0
    main.delete_task(one.id, db)
    assert a.tasks == [] and [t.id for t in b.tasks] == [two.id]
    assert all(t["statecode"] == 1 for t in remote.data["fs_incidenttemplatetask"].values() if t["name"] == "Changed")
    assert "fs_incidenttemplateproduct" not in remote.data


@pytest.mark.parametrize("payload", [{"name": " "}, {"name": "A", "estimated_duration_minutes": 0},
                                     {"name": "A", "estimated_duration_minutes": 1.5}])
def test_task_validation(payload):
    with pytest.raises(ValidationError):
        TaskInput(**payload)


def test_task_links_reject_invalid_without_partial_update(db, remote):
    one, two, a, b = catalog(db)
    for ids in ([one.id, one.id], [-99]):
        with pytest.raises(HTTPException):
            main._task_links(db, a, ids)
        assert [t.id for t in a.tasks] == [one.id]
    two.delete_flag = True; db.commit()
    with pytest.raises(HTTPException):
        main._task_links(db, a, [two.id])


def test_jobs_tasks_products_snapshots_and_repeat(db, remote):
    assignment, (one, two, a, b) = visit(db, remote)
    jobs.populate_work_order(db, remote, assignment)
    assert len(remote.data["fs_workorderincident"]) == 2
    assert {j["name"] for j in remote.data["fs_workorderincident"].values()} == {"General", "Winter"}
    assert len(remote.data["fs_workordertask"]) == 3
    assert len(remote.data["fs_workorderproduct"]) == 4
    assert all(t["__workorderid_id"] == assignment.resco_work_order_id and t["__workorderincidentid_id"] for t in remote.data["fs_workordertask"].values())
    first = next(iter(remote.data["fs_workordertask"].values()))
    first["completionpercent"] = 100
    one.name = "Later change"; db.commit()
    before = deepcopy(remote.data)
    jobs.populate_work_order(db, remote, assignment)
    assert remote.data == before


def test_partial_work_order_retry_reuses_snapshot(db, remote):
    assignment, (one, two, a, b) = visit(db, remote)
    remote.fail_entity = "fs_workordertask"
    with pytest.raises(RuntimeError):
        jobs.populate_work_order(db, remote, assignment)
    one.name = "Changed after snapshot"; db.commit()
    remote.fail_entity = None
    jobs.populate_work_order(db, remote, assignment)
    assert len(remote.data["fs_workorderincident"]) == 2
    assert len(remote.data["fs_workordertask"]) == 3
    assert "Changed after snapshot" not in [t["name"] for t in remote.data["fs_workordertask"].values()]


@pytest.mark.parametrize("product_type,count,expected", [("TJN", 1, 45), ("PRD", 1, None), ("TJN", 2, None)])
def test_visit_duration_on_single_service_line(db, remote, product_type, count, expected):
    assignment, _ = visit(db, remote)
    line = assignment.service_visit.contract_line
    line.required_products = line.required_products[:count]
    line.duration_minutes = 45
    for product in line.required_products:
        product.product_type = product_type
    jobs.populate_work_order(db, remote, assignment)
    products = list(remote.data["fs_workorderproduct"].values())
    assert all(p.get("estimatedduration") == expected for p in products)
    assert all(p["estimatedquantity"] == (expected or 1) for p in products)
    assert all("duration" not in p and "quantity" not in p for p in products)
    line.duration_minutes = 90
    products[0]["duration"] = 30
    before = deepcopy(remote.data)
    jobs.populate_work_order(db, remote, assignment)
    assert remote.data == before


def test_product_duration_survives_failed_create(db, remote):
    assignment, _ = visit(db, remote)
    line = assignment.service_visit.contract_line
    line.required_products = line.required_products[:1]
    line.duration_minutes = 45
    remote.fail_entity = "fs_workorderproduct"
    with pytest.raises(RuntimeError):
        jobs.populate_work_order(db, remote, assignment)
    line.duration_minutes = 90
    remote.fail_entity = None
    jobs.populate_work_order(db, remote, assignment)
    assert [p["estimatedduration"] for p in remote.data["fs_workorderproduct"].values()] == [45]


def test_ambiguous_create_response_recovers_same_id(db, remote):
    key = f"test:{uuid4()}"
    remote.lose_response = True
    with pytest.raises(TimeoutError):
        jobs.ensure(db, remote, key, "fs_workordertask", {"name": "Snapshot"})
    record = jobs.ensure(db, remote, key, "fs_workordertask", {"name": "Changed"})
    assert record.completed
    assert len(remote.posts) == 1
    assert remote.data["fs_workordertask"][record.remote_id]["name"] == "Snapshot"


def test_inactive_tasks_excluded_and_progress_stops_partial_retry(db, remote):
    assignment, (one, two, a, b) = visit(db, remote)
    b.task_links[1].delete_flag = True; db.commit()
    remote.fail_entity = "fs_workorderproduct"
    with pytest.raises(RuntimeError):
        jobs.populate_work_order(db, remote, assignment)
    assert len(remote.data["fs_workordertask"]) == 2
    task = next(iter(remote.data["fs_workordertask"].values()))
    task["completionpercent"] = 1
    before = deepcopy(remote.data)
    with pytest.raises(resco.RescoApiError, match="progress"):
        jobs.populate_work_order(db, remote, assignment)
    assert remote.data == before


def test_nok_setup_reuses_currency_and_validates_selection(db, monkeypatch):
    remote = Remote()
    monkeypatch.setattr(jobs.settings, "resco_nok_price_list_id", "")
    # Tests isolate the fixed setup key from any real remembered setup.
    db.query(RescoSyncRecord).filter_by(key="setup:nok-price-list").delete(); db.commit()
    with pytest.raises(resco.RescoApiError, match="NOK currency"):
        jobs.nok_setup(db, remote)
    currency = remote.add("transactioncurrency", isocurrencycode="NOK", exchangerate=9)
    result = jobs.nok_setup(db, remote)
    assert result[0] == currency["id"]
    assert jobs.nok_setup(db, remote) == result
    assert len(remote.data["pricelevel"]) == 1
    assert currency["exchangerate"] == 9
    remote.data["pricelevel"][result[1]]["__transactioncurrencyid_id"] = "USD"
    with pytest.raises(resco.RescoApiError, match="another currency"):
        jobs.nok_setup(db, remote)


def test_ambiguous_nok_price_lists_require_configuration(db, monkeypatch):
    remote = Remote()
    monkeypatch.setattr(jobs.settings, "resco_nok_price_list_id", "")
    db.query(RescoSyncRecord).filter_by(key="setup:nok-price-list").delete(); db.commit()
    currency = remote.add("transactioncurrency", isocurrencycode="NOK")
    for i in range(2):
        remote.add("pricelevel", __transactioncurrencyid_id=currency["id"])
    with pytest.raises(resco.RescoApiError, match="Multiple NOK"):
        jobs.nok_setup(db, remote)


@pytest.mark.parametrize("path,method", [("/tasks", "get"), ("/tasks", "post"),
    ("/tasks/1", "patch"), ("/tasks/1", "delete"), ("/products/sync-resco", "post"),
    ("/service-order-types/sync-resco", "post")])
def test_admin_routes_reject_anonymous(path, method):
    with TestClient(main.app) as client:
        assert getattr(client, method)(path).status_code in (401, 403)


def test_product_returned_failure_surfaces_warning(db, monkeypatch):
    monkeypatch.setattr(main, "_tripletex_client", lambda: NS(create_product=lambda payload: {"id": -987234}))
    monkeypatch.setattr(main, "sync_product", lambda *args: ProductRescoSyncResult(status="failed", detail="offline"))
    product = main.create_product(ProductCreate(name="Test product", number="9028123", product_type="TJN"), db)
    assert "Resco" in product.sync_warning
    assert db.get(Product, product.id).name == "Test product"


def test_seed_is_local_repeat_safe_and_preserves_later_edits(db):
    from scripts.seed_service_order_tasks import seed_tasks
    db.query(RescoSyncRecord).filter_by(key="seed:caretaker-tasks-v1").delete()
    targets = db.query(ServiceOrderType).filter(ServiceOrderType.name.in_(
        ["Generelle vaktmestertjenester", "Vaktmestertjenester (vinter)"])).all()
    for t in targets:
        t.name += " hidden by test"
    db.flush()
    with pytest.raises(ValueError, match="Expected one"):
        seed_tasks(db)
    a = ServiceOrderType(name="Generelle vaktmestertjenester")
    b = ServiceOrderType(name="Vaktmestertjenester (vinter)")
    db.add_all([a, b]); db.flush()
    assert seed_tasks(db)
    db.expire_all()
    assert [t.name for t in a.tasks] == ["generell inspeksjon"]
    assert [t.name for t in b.tasks] == ["generell inspeksjon", "lett snømåking"]
    assert a.tasks[0].id == b.tasks[0].id
    assert all(t.description is None and t.estimated_duration_minutes is None for t in b.tasks)
    a.task_links[0].delete_flag = True; db.flush()
    assert not seed_tasks(db)
    assert a.tasks == []


def test_cross_session_create_is_serialized():
    from concurrent.futures import ThreadPoolExecutor
    from app.database import SessionLocal
    from threading import Barrier
    key = f"test-concurrency:{uuid4()}"
    remote = Remote()
    barrier = Barrier(2)
    def worker():
        with SessionLocal() as db:
            barrier.wait(timeout=5)
            with jobs.sync_lock(db):
                return jobs.ensure(db, remote, key, "fs_incidenttemplate", {"name": "Concurrent"}).remote_id
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: worker(), range(2)))
        assert results[0] == results[1]
        assert len(remote.posts) == 1
    finally:
        with SessionLocal() as db:
            db.query(RescoSyncRecord).filter_by(key=key).delete(); db.commit()


def test_product_sync_by_identity_and_batch_failure_isolation(db, monkeypatch):
    client = NS(create_product=lambda p, setup: {"id": f"remote-{p.id}"}, update_product=lambda p, setup: {})
    monkeypatch.setattr(jobs, "sync_lock", lambda db: nullcontext())
    monkeypatch.setattr(jobs, "nok_setup", lambda *args: ("nok", "price"))
    monkeypatch.setattr(resco, "RescoClient", lambda *args: client)
    new = Product(name="New", number="test-new")
    archived = Product(name="Archived", number="test-old", archived=True)
    deleted = Product(name="Deleted", number="test-deleted", delete_flag=True)
    db.add_all([new, archived, deleted]); db.commit()
    assert resco.sync_product(db, new).status == "synced"
    rid = new.resco_product_id
    assert resco.sync_product(db, new).status == "synced"
    assert new.resco_product_id == rid
    seen = []
    def push(db, product):
        seen.append(product.id)
        return ProductRescoSyncResult(status="failed" if product.id == new.id else "synced", detail="test")
    monkeypatch.setattr(resco, "sync_product", push)
    result = resco.sync_products_to_resco(db)
    assert new.id in seen and archived.id not in seen and deleted.id not in seen
    assert result.failed == 1 and len(seen) > 1


@pytest.mark.parametrize("product_type,isservice", [("TJN", True), ("PRD", False)])
@pytest.mark.parametrize("existing", [False, True])
def test_product_service_and_nok_defaults_on_create_and_update(db, monkeypatch, product_type, isservice, existing):
    import httpx

    requests = []
    def respond(request):
        import json
        requests.append((request.method, json.loads(request.content)))
        return httpx.Response(200, json={"id": "remembered"})

    real_client = httpx.Client
    monkeypatch.setattr(resco.httpx, "Client", lambda **kwargs: real_client(
        transport=httpx.MockTransport(respond), **kwargs))
    monkeypatch.setattr(jobs, "sync_lock", lambda db: nullcontext())
    monkeypatch.setattr(jobs, "nok_setup", lambda *args: ("nok", "price"))
    product = Product(name="Mapped product", number="mapping-test", product_type=product_type,
                      resco_product_id="remembered" if existing else None)
    db.add(product); db.commit()
    assert resco.sync_product(db, product).status == "synced"
    assert product.resco_product_id == "remembered"
    assert requests == [("PATCH" if existing else "POST", {
        "name": "Mapped product", "productnumber": "mapping-test", "isservice": isservice,
        "transactioncurrencyid_transactioncurrency@odata.bind": "/transactioncurrency(nok)",
        "pricelevelid_pricelevel@odata.bind": "/pricelevel(price)",
    })]


def test_product_setup_failure_preserves_identity_without_remote_write(db, monkeypatch):
    monkeypatch.setattr(jobs, "sync_lock", lambda db: nullcontext())
    def fail(*args):
        raise jobs.RescoApiError("Configure exactly one active NOK currency in Resco")
    monkeypatch.setattr(jobs, "nok_setup", fail)
    calls = []
    monkeypatch.setattr(resco.RescoClient, "update_product", lambda *args: calls.append(args))
    product = Product(name="Preserved", number="setup-failure", resco_product_id="remembered")
    db.add(product); db.commit()
    result = resco.sync_product(db, product)
    assert result.status == "failed" and "NOK" in result.detail
    db.refresh(product)
    assert product.resco_product_id == "remembered" and product.name == "Preserved"
    assert calls == []


def test_existing_job_and_tasks_are_adopted_without_duplicates(db, remote):
    assignment, (one, two, a, b) = visit(db, remote)
    jobs.populate_work_order(db, remote, assignment)
    before = deepcopy(remote.data)
    wo = assignment.resco_work_order_id
    for record in db.query(RescoSyncRecord).all():
        if wo in record.key:
            db.delete(record)
    db.commit()
    jobs.populate_work_order(db, remote, assignment, catch_up=True)
    for entity in ("fs_workorderincident", "fs_workordertask", "fs_workorderproduct"):
        assert remote.data[entity] == before[entity]


@pytest.mark.parametrize("path", ["/tasks", "/products/sync-resco", "/service-order-types/sync-resco"])
def test_non_admin_is_denied(path):
    from app.auth import get_current_user
    main.app.dependency_overrides[get_current_user] = lambda: NS(is_admin=False)
    try:
        with TestClient(main.app) as client:
            assert client.post(path, json={"name": "Forbidden"}).status_code == 403
    finally:
        main.app.dependency_overrides.pop(get_current_user, None)


def test_selected_catchup_preview_apply_and_repeat(db, remote, monkeypatch):
    from app.models import Assignment
    from scripts.catch_up_resco_jobs import catch_up
    assignment, _ = visit(db, remote)
    assignment.resco_work_order_schedule_id = remote.add(
        "fs_workorderschedule", __workorderid_id=assignment.resco_work_order_id,
        scheduledstart="2026-09-24T08:00:00+02:00", __resourceid_id="worker",
    )["id"]
    get, refresh = db.get, db.refresh
    monkeypatch.setattr(db, "get", lambda model, id: assignment if model is Assignment else get(model, id))
    monkeypatch.setattr(db, "refresh", lambda obj: None if obj is assignment else refresh(obj))
    original_schedule = deepcopy(remote.data["fs_workorderschedule"])
    before = db.query(RescoSyncRecord).count()
    assert catch_up(db, remote, 123)["status"] == "preview"
    assert remote.posts == [] and db.query(RescoSyncRecord).count() == before
    assert catch_up(db, remote, 123, apply=True)["status"] == "applied"
    assert catch_up(db, remote, 123)["detail"] == "Already populated"
    assert remote.data["fs_workorderschedule"] == original_schedule


def test_catchup_rejects_progress_and_conflicting_currency(db, remote, monkeypatch):
    from app.models import Assignment
    from scripts.catch_up_resco_jobs import catch_up
    assignment, _ = visit(db, remote)
    assignment.resco_work_order_schedule_id = remote.add(
        "fs_workorderschedule", __workorderid_id=assignment.resco_work_order_id,
    )["id"]
    get, refresh = db.get, db.refresh
    monkeypatch.setattr(db, "get", lambda model, id: assignment if model is Assignment else get(model, id))
    monkeypatch.setattr(db, "refresh", lambda obj: None if obj is assignment else refresh(obj))
    parent = remote.data["fs_workorder"][assignment.resco_work_order_id]
    parent["__transactioncurrencyid_id"] = "USD"
    assert catch_up(db, remote, 123, apply=True)["status"] == "skipped"
    parent["statuscode"] = 6
    assert catch_up(db, remote, 123, apply=True)["status"] == "skipped"
    assert remote.posts == [] and remote.patches == []


def test_full_assignment_sync_retries_schedule_failure_and_populates(db, remote, monkeypatch):
    from app.models import Assignment
    assignment = db.query(Assignment).first()
    if assignment is None:
        pytest.skip("Requires a dev assignment with synced customer/employee")
    _, _, type_, _ = catalog(db)
    for product in assignment.service_visit.contract_line.required_products:
        product.service_order_type = type_
    db.commit()
    original_client = resco.RescoClient
    remote._work_order_payload = original_client._work_order_payload
    remote._work_order_schedule_payload = original_client._work_order_schedule_payload
    remote._work_order_schedule_name = original_client._work_order_schedule_name
    remote.find_resource_id_for_user = lambda user_id: "worker"
    remote.update_work_order = lambda item: original_client.update_work_order(remote, item)
    remote.update_work_order_schedule = lambda item, resource: remote._request(
        "PATCH", f"fs_workorderschedule('{item.resco_work_order_schedule_id}')",
        json=original_client._work_order_schedule_payload(item, resource))
    monkeypatch.setattr(resco, "RescoClient", lambda *args: remote)
    assignment.resco_work_order_id = None
    assignment.resco_work_order_schedule_id = None
    assignment.resco_sync_token = None
    db.commit()
    remote.fail_entity = "fs_workorderschedule"
    assert resco.sync_assignment(db, assignment).status == "failed"
    parent_id = assignment.resco_work_order_id
    assert parent_id and assignment.resco_work_order_schedule_id is None
    remote.fail_entity = None
    result = resco.sync_assignment(db, assignment)
    assert result.status == "synced", result.detail
    assert assignment.resco_work_order_id == parent_id
    assert remote.data["fs_workorder"][parent_id]["__transactioncurrencyid_id"] == "nok"
    assert len(remote.data["fs_workorder"]) == 1 and len(remote.data["fs_workorderschedule"]) == 1
    assert remote.data.get("fs_workorderincident") and remote.data.get("fs_workordertask")
    before = deepcopy(remote.data["fs_workordertask"])
    result = resco.sync_assignment(db, assignment)
    assert result.status == "synced", result.detail
    assert before == remote.data["fs_workordertask"]
