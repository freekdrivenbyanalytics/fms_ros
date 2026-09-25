"""Template synchronization and immutable Work Order job/task snapshots."""
from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RescoSyncRecord, ServiceOrderType
from app.resco import RescoApiError, RescoClient, sync_product
from app.schemas import RescoSyncSummary


class RescoSyncConflict(RescoApiError):
    pass


@contextmanager
def sync_lock(db: Session):
    # A dedicated connection keeps the lock across the identity-persistence commits.
    # Serialize this integration across API workers, including setup and catch-up.
    with db.get_bind().connect() as connection:
        connection.execute(text("SELECT pg_advisory_lock(7281940028)"))
        try:
            yield
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(7281940028)"))


def client_for_resco() -> RescoClient:
    return RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)


def rows(client: RescoClient, entity: str, filter_: str) -> list[dict]:
    result = client._request("GET", entity, params={"$filter": filter_})
    if not isinstance(result, dict) or not isinstance(result.get("value"), list):
        raise RescoApiError("Invalid Resco collection response")
    found = result["value"]
    while result.get("@odata.nextLink"):
        url = result["@odata.nextLink"]
        prefix = client._base_url + "/"
        if not url.startswith(prefix):
            raise RescoApiError("Unexpected Resco pagination URL")
        result = client._request("GET", url[len(prefix):])
        found.extend(result["value"])
    return found


def by_id(client: RescoClient, entity: str, remote_id: str) -> dict | None:
    found = rows(client, entity, "id eq '" + remote_id.replace("'", "''") + "'")
    if len(found) > 1:
        raise RescoApiError(f"Ambiguous {entity} identity")
    return found[0] if found else None


def bind(entity: str, remote_id: str) -> str:
    return f"/{entity}({remote_id})"


def reserve(db: Session, key: str, entity: str, payload: dict,
            remote_id: str | None = None) -> RescoSyncRecord:
    record = db.get(RescoSyncRecord, key)
    if record is None:
        record = RescoSyncRecord(key=key, entity=entity, remote_id=remote_id or str(uuid4()),
                                 payload=payload, completed=False)
        db.add(record)
        db.commit()
    return record


def ensure(db: Session, client: RescoClient, key: str, entity: str, payload: dict,
           *, mutable: bool = False, remote_id: str | None = None) -> RescoSyncRecord:
    record = reserve(db, key, entity, payload, remote_id)
    remote = by_id(client, entity, record.remote_id)
    if remote is None:
        if record.completed:
            raise RescoApiError(f"Previously synced {entity} {record.remote_id} is missing")
        client._request("POST", entity, json={"id": record.remote_id, **record.payload})
    elif not mutable:
        for field, expected in record.payload.items():
            if field.endswith("@odata.bind"):
                target, identifier = expected[1:-1].split("(", 1)
                lookup = field.removesuffix("@odata.bind").removesuffix("_" + target)
                if remote.get("__" + lookup + "_id") != identifier:
                    raise RescoSyncConflict(f"Existing {entity} has a conflicting {lookup} link")
    elif mutable:
        client._request("PATCH", f"{entity}('{record.remote_id}')", json=payload,
                        headers={"If-Match": remote["@odata.etag"]})
    if mutable:
        # Handles an edit after an ambiguous/failed create using its original payload.
        if remote is None and record.payload != payload:
            client._request("PATCH", f"{entity}('{record.remote_id}')", json=payload)
        record.payload = payload
    record.completed = True
    db.commit()
    return record


def nok_setup(db: Session, client: RescoClient, *, create: bool = True) -> tuple[str, str | None]:
    currencies = rows(client, "transactioncurrency", "isocurrencycode eq 'NOK' and statecode eq 0")
    if len(currencies) != 1:
        raise RescoApiError("Configure exactly one active NOK currency in Resco")
    currency = currencies[0]["id"]
    remembered = db.get(RescoSyncRecord, "setup:nok-price-list")
    selected = settings.resco_nok_price_list_id or (remembered.remote_id if remembered else None)
    if selected:
        price = by_id(client, "pricelevel", selected)
        if price:
            if price.get("statecode") != 0 or price.get("__transactioncurrencyid_id") != currency:
                raise RescoApiError("Configured NOK price list is inactive or uses another currency")
            return currency, selected
        if settings.resco_nok_price_list_id or remembered.completed:
            raise RescoApiError("Configured NOK price list is missing")
    else:
        prices = rows(client, "pricelevel", f"__transactioncurrencyid_id eq '{currency}' and statecode eq 0")
        if len(prices) > 1:
            raise RescoApiError("Multiple NOK price lists; configure RESCO_NOK_PRICE_LIST_ID")
        if prices:
            if create:
                record = reserve(db, "setup:nok-price-list", "pricelevel", {}, prices[0]["id"])
                record.completed = True
                db.commit()
            return currency, prices[0]["id"]
    if not create:
        return currency, None
    price = ensure(db, client, "setup:nok-price-list", "pricelevel", {
        "name": "NOK", "statecode": 0, "statuscode": 100001,
        "transactioncurrencyid_transactioncurrency@odata.bind": bind("transactioncurrency", currency),
    })
    return currency, price.remote_id


def pricing(currency: str, price: str) -> dict:
    return {"transactioncurrencyid_transactioncurrency@odata.bind": bind("transactioncurrency", currency),
            "pricelevelid_pricelevel@odata.bind": bind("pricelevel", price)}


def sync_template(db: Session, client: RescoClient, type_: ServiceOrderType,
                  setup: tuple[str, str]) -> str | None:
    if type_.delete_flag and not type_.resco_job_template_id and not db.get(
        RescoSyncRecord, f"template:{type_.id}"
    ):
        return None
    template = ensure(db, client, f"template:{type_.id}", "fs_incidenttemplate", {
        "name": type_.name, **pricing(*setup),
        "statecode": 1 if type_.delete_flag else 0,
        "statuscode": 2 if type_.delete_flag else 1,
    }, mutable=True, remote_id=type_.resco_job_template_id)
    type_.resco_job_template_id = template.remote_id
    db.commit()
    for link in type_.task_links:
        inactive = link.delete_flag or link.task.delete_flag or type_.delete_flag
        key = f"template-task:{type_.id}:{link.task_id}"
        if inactive and not link.resco_task_id and not db.get(RescoSyncRecord, key):
            continue
        task = ensure(db, client, key, "fs_incidenttemplatetask", {
            "name": link.task.name, "description": link.task.description,
            "duration": link.task.estimated_duration_minutes, "fs_taskorder": link.position + 1,
            "incidenttemplateid_fs_incidenttemplate@odata.bind": bind("fs_incidenttemplate", template.remote_id),
            "statecode": 1 if inactive else 0, "statuscode": 2 if inactive else 1,
        }, mutable=True, remote_id=link.resco_task_id)
        link.resco_task_id = task.remote_id
        db.commit()
    type_.sync_error = None
    db.commit()
    return template.remote_id


def sync_types(db: Session, type_ids: list[int] | None = None) -> RescoSyncSummary:
    summary = RescoSyncSummary(created=0, updated=0, skipped=0, failed=0, errors=[])
    query = db.query(ServiceOrderType)
    if type_ids is not None:
        query = query.filter(ServiceOrderType.id.in_(type_ids))
    ids = [t.id for t in query.all()]
    for type_id in ids:
        try:
            with sync_lock(db):
                db.expire_all()
                type_ = db.get(ServiceOrderType, type_id)
                was_new = not type_.resco_job_template_id
                result = sync_template(db, client_for_resco(), type_, nok_setup(db, client_for_resco()))
                if result is None:
                    summary.skipped += 1
                elif was_new:
                    summary.created += 1
                else:
                    summary.updated += 1
        except Exception as exc:
            db.rollback()
            type_ = db.get(ServiceOrderType, type_id)
            type_.sync_error = str(exc)
            db.commit()
            summary.failed += 1
            summary.errors.append(f"{type_.name}: {exc}")
    return summary


def selected_products(assignment):
    return sorted((p for p in assignment.service_visit.contract_line.required_products
                   if not p.delete_flag and not p.archived), key=lambda p: p.id)


def make_manifest(db: Session, client: RescoClient, assignment, setup) -> dict:
    products = selected_products(assignment)
    types = {p.service_order_type.id: p.service_order_type for p in products
             if p.service_order_type and not p.service_order_type.delete_flag}
    jobs = []
    for type_ in types.values():
        template_id = sync_template(db, client, type_, setup)
        jobs.append({"type_id": type_.id, "template_id": template_id, "name": type_.name,
                     "tasks": [{"id": task.id, "name": task.name, "description": task.description,
                                "estimatedduration": task.estimated_duration_minutes,
                                "fs_taskorder": pos + 1} for pos, task in enumerate(type_.tasks)]})
    product_data = []
    for product in products:
        result = sync_product(db, product, setup=setup)
        if result.status != "synced":
            raise RescoApiError(f"Product {product.name}: {result.detail}")
        product_data.append({"id": product.id, "remote_id": product.resco_product_id,
                             "type_id": product.service_order_type_id,
                             "isservice": product.product_type == "TJN"})
        # A single service represents the whole visit; multiple products need an allocation rule.
        if len(products) == 1 and product.product_type == "TJN":
            product_data[-1]["estimatedduration"] = assignment.service_visit.contract_line.duration_minutes
    return {"jobs": jobs, "products": product_data, "currency": setup[0], "price": setup[1]}


def verify_unprogressed(client: RescoClient, work_order_id: str) -> dict:
    parent = client._request("GET", f"fs_workorder('{work_order_id}')")
    if (parent.get("statecode"), parent.get("statuscode")) != (0, 5):
        raise RescoSyncConflict("Work Order is no longer Active/Scheduled; skipped")
    for entity in ("fs_workorderincident", "fs_workordertask", "fs_workorderproduct"):
        for row in rows(client, entity, f"__workorderid_id eq '{work_order_id}'"):
            if row.get("statecode", 0) != 0 or row.get("statuscode", 1) != 1 or any(
                row.get(field) for field in ("completionpercent", "totalduration", "quantity", "isused")
            ):
                raise RescoSyncConflict("Work Order has task/job/product progress; skipped")
    return parent


def populate_work_order(db: Session, client: RescoClient, assignment, *, catch_up=False) -> None:
    """Caller holds sync_lock. Legacy orders require explicit catch-up."""
    wo = assignment.resco_work_order_id
    key = f"work-order:{wo}"
    manifest = db.get(RescoSyncRecord, key)
    if manifest and manifest.completed:
        return
    parent = verify_unprogressed(client, wo)
    setup = nok_setup(db, client)
    if catch_up:
        if parent.get("__transactioncurrencyid_id") not in (None, setup[0]):
            raise RescoSyncConflict("Existing Work Order uses another currency; skipped")
        price_id = parent.get("__pricelevelid_id")
        if price_id:
            price = by_id(client, "pricelevel", price_id)
            if not price or price.get("__transactioncurrencyid_id") != setup[0]:
                raise RescoSyncConflict("Existing Work Order has conflicting pricing; skipped")
    if manifest is None:
        manifest = reserve(db, key, "manifest", make_manifest(db, client, assignment, setup), wo)
    data = manifest.payload
    patch = {}
    if not parent.get("__pricelevelid_id"):
        patch["pricelevelid_pricelevel@odata.bind"] = bind("pricelevel", data["price"])
    if not parent.get("__transactioncurrencyid_id"):
        patch["transactioncurrencyid_transactioncurrency@odata.bind"] = bind("transactioncurrency", data["currency"])
    if patch:
        client._request("PATCH", f"fs_workorder('{wo}')", json=patch,
                        headers={"If-Match": parent["@odata.etag"]})
    job_ids = {}
    for job in data["jobs"]:
        verify_unprogressed(client, wo)
        job_key = f"job:{wo}:{job['type_id']}"
        remembered = db.get(RescoSyncRecord, job_key)
        if remembered is None:
            matches = rows(client, "fs_workorderincident",
                           f"__workorderid_id eq '{wo}' and __incidenttemplateid_id eq '{job['template_id']}'")
            if len(matches) > 1:
                raise RescoSyncConflict("Multiple matching jobs; cannot safely infer ownership")
            if matches:
                existing = matches[0]
                existing_tasks = rows(client, "fs_workordertask",
                                      f"__workorderincidentid_id eq '{existing['id']}'")
                remaining = list(existing_tasks)
                adopted = []
                for task in job["tasks"]:
                    candidates = [t for t in remaining if all(t.get(k) == task.get(k)
                                  for k in ("name", "description", "estimatedduration", "fs_taskorder"))]
                    if len(candidates) > 1:
                        raise RescoSyncConflict("Ambiguous existing task identity; skipped")
                    if candidates:
                        adopted.append((task, candidates[0]))
                        remaining.remove(candidates[0])
                if remaining:
                    raise RescoSyncConflict("Existing job has conflicting task contents; skipped")
                reserve(db, job_key, "fs_workorderincident", {}, existing["id"])
                for task, remote_task in adopted:
                    reserve(db, f"job-task:{wo}:{job['type_id']}:{task['id']}",
                            "fs_workordertask", {}, remote_task["id"])
        record = ensure(db, client, job_key, "fs_workorderincident", {
            "name": job["name"], "workorderid_fs_workorder@odata.bind": bind("fs_workorder", wo),
            "incidenttemplateid_fs_incidenttemplate@odata.bind": bind("fs_incidenttemplate", job["template_id"]),
        })
        job_ids[job["type_id"]] = record.remote_id
        for task in job["tasks"]:
            verify_unprogressed(client, wo)
            ensure(db, client, f"job-task:{wo}:{job['type_id']}:{task['id']}", "fs_workordertask", {
                **{k: v for k, v in task.items() if k != "id"},
                "workorderid_fs_workorder@odata.bind": bind("fs_workorder", wo),
                "workorderincidentid_fs_workorderincident@odata.bind": bind("fs_workorderincident", record.remote_id),
            })
    for product in data["products"]:
        verify_unprogressed(client, wo)
        payload = {"productid_product@odata.bind": bind("product", product["remote_id"]),
                   "workorderid_fs_workorder@odata.bind": bind("fs_workorder", wo),
                   "transactioncurrencyid_transactioncurrency@odata.bind": bind("transactioncurrency", data["currency"]),
                   "estimatedquantity": 1, "isservice": product["isservice"]}
        if "estimatedduration" in product:
            payload["estimatedduration"] = product["estimatedduration"]
            # Resco's service list renders estimatedquantity as minutes, not units.
            payload["estimatedquantity"] = product["estimatedduration"]
        if product["type_id"] in job_ids:
            payload["workorderincidentid_fs_workorderincident@odata.bind"] = bind("fs_workorderincident", job_ids[product["type_id"]])
        line_key = f"product-line:{wo}:{product['id']}"
        if db.get(RescoSyncRecord, line_key) is None:
            existing = rows(client, "fs_workorderproduct",
                            f"__workorderid_id eq '{wo}' and __productid_id eq '{product['remote_id']}'")
            if len(existing) > 1:
                raise RescoSyncConflict("Multiple matching product lines; skipped")
            if existing:
                expected_job = job_ids.get(product["type_id"])
                if existing[0].get("__workorderincidentid_id") != expected_job:
                    raise RescoSyncConflict("Existing product line has a conflicting job; skipped")
                reserve(db, line_key, "fs_workorderproduct", {}, existing[0]["id"])
        ensure(db, client, line_key, "fs_workorderproduct", payload)
    manifest.completed = True
    db.commit()
