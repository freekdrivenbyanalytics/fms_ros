"""Preview selected portal Work Orders; --apply adds missing jobs/tasks/products/NOK pricing."""
import argparse
import json

from app.database import SessionLocal
from app.models import Assignment, RescoSyncRecord
from app.resco_jobs import (
    RescoSyncConflict, by_id, client_for_resco, nok_setup, populate_work_order, rows, selected_products,
    sync_lock, verify_unprogressed,
)


def catch_up(db, client, visit_id: int, *, apply=False) -> dict:
    result = {"visit_id": visit_id, "status": "skipped"}
    assignment = db.get(Assignment, visit_id)
    if not assignment or not assignment.resco_work_order_id or not assignment.resco_work_order_schedule_id:
        return result | {"detail": "No portal assignment with remembered Work Order and schedule IDs"}
    wo = assignment.resco_work_order_id
    result["work_order_id"] = wo
    try:
        with sync_lock(db):
            db.refresh(assignment)
            if assignment.resco_work_order_id != wo:
                return result | {"detail": "Assignment changed; preview again"}
            manifest = db.get(RescoSyncRecord, f"work-order:{wo}")
            if manifest and manifest.completed:
                return result | {"detail": "Already populated"}
            parent = verify_unprogressed(client, wo)
            schedule = by_id(client, "fs_workorderschedule", assignment.resco_work_order_schedule_id)
            if not schedule or schedule.get("__workorderid_id") != wo or (
                schedule.get("statecode"), schedule.get("statuscode")
            ) != (0, 1):
                return result | {"detail": "Schedule identity/state differs from portal assignment"}
            currency, price = nok_setup(db, client, create=False)
            if parent.get("__transactioncurrencyid_id") not in (None, currency):
                return result | {"detail": "Existing non-NOK currency"}
            existing_price = parent.get("__pricelevelid_id")
            if existing_price:
                row = by_id(client, "pricelevel", existing_price)
                if not row or row.get("statecode") != 0 or row.get("__transactioncurrencyid_id") != currency:
                    return result | {"detail": "Conflicting/inactive price list"}
            products = selected_products(assignment)
            types = {p.service_order_type.id: p.service_order_type for p in products
                     if p.service_order_type and not p.service_order_type.delete_flag}
            jobs = rows(client, "fs_workorderincident", f"__workorderid_id eq '{wo}'")
            result["changes"] = {
                "set_nok_currency": not parent.get("__transactioncurrencyid_id"),
                "set_nok_price_list": not existing_price,
                "create_nok_price_list": not price,
                "job_templates": [t.name for t in types.values()],
                "task_names": {t.name: [task.name for task in t.tasks] for t in types.values()},
                "product_ids": [p.id for p in products],
                "existing_job_count": len(jobs),
                "resume_snapshot": bool(manifest),
            }
            if not apply:
                return result | {"status": "preview"}
            populate_work_order(db, client, assignment, catch_up=True)
            return result | {"status": "applied"}
    except RescoSyncConflict as exc:
        db.rollback()
        return result | {"detail": str(exc)}
    except Exception as exc:
        db.rollback()
        return result | {"status": "failed", "detail": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visit_ids", nargs="+", type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        results = [catch_up(db, client_for_resco(), visit_id, apply=args.apply)
                   for visit_id in dict.fromkeys(args.visit_ids)]
    print(json.dumps(results, indent=2, ensure_ascii=False))
    if any(r["status"] == "failed" for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
