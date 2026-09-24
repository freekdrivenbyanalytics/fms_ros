"""Preview selected portal schedules; pass --apply to repair eligible New bookings."""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Assignment
from app.resco import RescoClient, _to_resco_datetime


def repair_schedule(db: Session, client: RescoClient, visit_id: int, *, apply: bool = False) -> dict:
    result = {"visit_id": visit_id, "status": "skipped"}
    assignment = db.get(Assignment, visit_id)
    if not assignment or not assignment.resco_work_order_id or not assignment.resco_work_order_schedule_id:
        return result | {"detail": "No portal assignment with both remembered Resco IDs"}
    try:
        parent_path = f"fs_workorder('{assignment.resco_work_order_id}')"
        child_path = f"fs_workorderschedule('{assignment.resco_work_order_schedule_id}')"
        parent = client.get_work_order_status(assignment.resco_work_order_id)
        child = client._request("GET", child_path)
        if (parent.get("statecode"), parent.get("statuscode")) != (0, 5):
            return result | {"detail": "Work Order is not Active/Scheduled"}
        if (child.get("statecode"), child.get("statuscode")) != (0, 0):
            return result | {"detail": "Schedule is not Active/New"}
        if child.get("id") != assignment.resco_work_order_schedule_id or child.get("__workorderid_id") != assignment.resco_work_order_id:
            return result | {"detail": "Schedule identity or parent link does not match"}
        if not assignment.employee.resco_user_id:
            return result | {"detail": "Employee has no Resco User ID"}
        resource_id = client.find_resource_id_for_user(assignment.employee.resco_user_id)
        if child.get("__resourceid_id") != resource_id:
            return result | {"detail": "Schedule resource differs from portal assignment"}
        for field, value in (("scheduledstart", assignment.planned_start), ("scheduledend", assignment.planned_end)):
            remote = datetime.fromisoformat(child.get(field) or "")
            if remote.tzinfo is None or remote != datetime.fromisoformat(_to_resco_datetime(value)):
                return result | {"detail": f"{field} differs from portal assignment"}
        if not child.get("@odata.etag") or not parent.get("@odata.etag"):
            return result | {"detail": "Missing remote version; cannot safely repair"}
        payload = {"statecode": 0, "statuscode": 1}
        if not child.get("name"):
            payload["name"] = client._work_order_schedule_name(assignment)
        result |= {"work_order_id": assignment.resco_work_order_id,
                   "schedule_id": assignment.resco_work_order_schedule_id, "changes": payload}
        if not apply:
            return result | {"status": "preview"}
        # The parent cannot be atomically checked with the child PATCH; recheck it last.
        current_parent = client._request("GET", parent_path)
        if current_parent.get("@odata.etag") != parent["@odata.etag"] or (
            current_parent.get("statecode"), current_parent.get("statuscode")
        ) != (0, 5):
            return result | {"detail": "Work Order changed during repair; retry preview"}
        client._request("PATCH", child_path, json=payload,
                        headers={"If-Match": child["@odata.etag"]})
        return result | {"status": "repaired"}
    except Exception as exc:
        return result | {"status": "failed", "detail": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visit_ids", nargs="+", type=int)
    parser.add_argument("--apply", action="store_true", help="Write the previewed repairs to Resco")
    args = parser.parse_args()
    client = RescoClient(settings.resco_base_url, settings.resco_username, settings.resco_password)
    with SessionLocal() as db:
        results = [repair_schedule(db, client, visit_id, apply=args.apply)
                   for visit_id in dict.fromkeys(args.visit_ids)]
    print(json.dumps({"results": results, "counts": {
        status: sum(item["status"] == status for item in results)
        for status in ("preview", "repaired", "skipped", "failed")
    }}, indent=2))
    if any(item["status"] == "failed" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
