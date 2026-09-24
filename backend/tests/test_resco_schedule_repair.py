from datetime import datetime
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

import pytest

from scripts.repair_resco_schedules import repair_schedule


def fixture():
    assignment = NS(resco_work_order_id="parent", resco_work_order_schedule_id="child",
                    employee=NS(resco_user_id="user"), planned_start=datetime(2026, 9, 24, 14),
                    planned_end=datetime(2026, 9, 24, 15))
    db, client = MagicMock(), MagicMock()
    db.get.return_value = assignment
    parent = {"id": "parent", "statecode": 0, "statuscode": 5, "@odata.etag": 'W/"parent"'}
    child = {"id": "child", "__workorderid_id": "parent", "__resourceid_id": "resource",
             "statecode": 0, "statuscode": 0, "name": None, "@odata.etag": 'W/"child"',
             "scheduledstart": "2026-09-24T12:00:00Z", "scheduledend": "2026-09-24T13:00:00Z"}
    client.get_work_order_status.return_value = parent
    client.find_resource_id_for_user.return_value = "resource"
    client._work_order_schedule_name.return_value = "SCH-visit"
    def request(method, path, **kwargs):
        if method == "PATCH":
            child.update(kwargs["json"])
            return child
        return child if path.startswith("fs_workorderschedule") else parent
    client._request.side_effect = request
    return db, client, assignment, parent, child


def test_preview_apply_and_repeat_preserve_identity_and_booking():
    db, client, assignment, parent, child = fixture()
    before = child.copy()
    assert repair_schedule(db, client, 1)["status"] == "preview"
    assert child == before
    result = repair_schedule(db, client, 1, apply=True)
    assert result["status"] == "repaired"
    writes = [call for call in client._request.call_args_list if call.args[0] == "PATCH"]
    assert len(writes) == 1
    assert writes[0].kwargs["headers"] == {"If-Match": 'W/"child"'}
    assert writes[0].kwargs["json"] == {"statecode": 0, "statuscode": 1, "name": "SCH-visit"}
    for key in ("id", "__workorderid_id", "__resourceid_id", "scheduledstart", "scheduledend"):
        assert child[key] == before[key]
    assert repair_schedule(db, client, 1, apply=True)["status"] == "skipped"
    db.commit.assert_not_called()


@pytest.mark.parametrize("field,value", [
    ("statuscode", 4), ("statecode", 1), ("__workorderid_id", "other"),
    ("id", "other"), ("__resourceid_id", "other"),
    ("scheduledstart", "2026-09-24T13:00:00Z"), ("@odata.etag", None),
])
def test_ineligible_child_is_never_written(field, value):
    db, client, _, _, child = fixture()
    child[field] = value
    assert repair_schedule(db, client, 1, apply=True)["status"] == "skipped"
    assert all(call.args[0] != "PATCH" for call in client._request.call_args_list)


def test_missing_portal_link_does_not_read_external_orders():
    db, client, *_ = fixture()
    db.get.return_value = None
    assert repair_schedule(db, client, 1, apply=True)["status"] == "skipped"
    client.get_work_order_status.assert_not_called()
    client._request.assert_not_called()


def test_progressed_parent_is_skipped():
    db, client, _, parent, _ = fixture()
    parent["statuscode"] = 10001
    assert repair_schedule(db, client, 1, apply=True)["status"] == "skipped"
    assert all(call.args[0] != "PATCH" for call in client._request.call_args_list)


def test_concurrent_parent_change_is_skipped():
    db, client, _, parent, child = fixture()
    client._request.side_effect = [child, parent | {"@odata.etag": "changed"}]
    assert repair_schedule(db, client, 1, apply=True)["status"] == "skipped"
    assert all(call.args[0] != "PATCH" for call in client._request.call_args_list)


@pytest.mark.parametrize("error", ["412 Precondition Failed", "offline"])
def test_failed_conditional_write_is_reported_without_retry(error):
    db, client, _, parent, child = fixture()
    client._request.side_effect = [child, parent, RuntimeError(error)]
    result = repair_schedule(db, client, 1, apply=True)
    assert result["status"] == "failed" and error in result["detail"]
    assert sum(call.args[0] == "PATCH" for call in client._request.call_args_list) == 1
