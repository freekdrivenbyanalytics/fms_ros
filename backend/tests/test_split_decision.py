from unittest.mock import patch

from app.solver_client import _RunData, _group_payloads_from_data, _should_attempt_split


class _Region:
    def __init__(self, id: int) -> None:
        self.id = id


class _Employee:
    def __init__(self, id: int, region_ids: list[int]) -> None:
        self.id = id
        self.regions = [_Region(region_id) for region_id in region_ids]


class _Location:
    def __init__(self, region_id: int) -> None:
        self.region_id = region_id


class _ContractLine:
    def __init__(self, region_id: int) -> None:
        self.customer_location = _Location(region_id)


class _Visit:
    def __init__(self, id: int, region_id: int) -> None:
        self.id = id
        self.contract_line = _ContractLine(region_id)


def _run_data(employees: list, ready_visits: list) -> _RunData:
    return _RunData(
        employees=employees,
        ready_visits=ready_visits,
        locked_assignments=[],
        excluded_visit_ids=[],
        candidate_dates=set(),
        all_region_ids=set(),
        previous_occurrence_by_visit_id={},
    )


@patch("app.solver_client.settings.parallel_split_visit_threshold", 75)
def test_below_threshold_without_force_does_not_split() -> None:
    assert _should_attempt_split(ready_visit_count=50, force_split=False) is False


@patch("app.solver_client.settings.parallel_split_visit_threshold", 75)
def test_above_threshold_without_force_attempts_split() -> None:
    assert _should_attempt_split(ready_visit_count=100, force_split=True) is True
    assert _should_attempt_split(ready_visit_count=100, force_split=False) is True


@patch("app.solver_client.settings.parallel_split_visit_threshold", 75)
def test_force_split_attempts_split_regardless_of_threshold() -> None:
    assert _should_attempt_split(ready_visit_count=1, force_split=True) is True


@patch("app.solver_client.settings.parallel_split_visit_threshold", 75)
def test_exactly_at_threshold_does_not_split() -> None:
    # The threshold is exceeded, not met, per design.md's "exceeds the
    # threshold" wording.
    assert _should_attempt_split(ready_visit_count=75, force_split=False) is False


def test_above_threshold_but_fully_connected_regions_fall_back_to_unsplit() -> None:
    # Even when a split is attempted (e.g. above the threshold), a region
    # graph with no genuine split point (every region reachable from every
    # other through shared employees) must fall back to None, matching
    # build_parallel_group_payloads' own fallback - the caller then solves
    # the whole run as one problem instead.
    employees = [_Employee(1, [1, 2])]
    ready_visits = [_Visit(1, region_id=1), _Visit(2, region_id=2)]
    data = _run_data(employees, ready_visits)

    group_payloads = _group_payloads_from_data(
        db=None, data=data, time_limit_seconds=None, plan_from_time=None
    )

    assert group_payloads is None


def test_disjoint_regions_produce_one_payload_per_group() -> None:
    employees = [_Employee(1, [1]), _Employee(2, [2])]
    ready_visits = [_Visit(1, region_id=1), _Visit(2, region_id=2)]
    data = _run_data(employees, ready_visits)

    with patch("app.solver_client._assemble_payload", side_effect=lambda *a, **k: {"stub": True}):
        group_payloads = _group_payloads_from_data(
            db=None, data=data, time_limit_seconds=None, plan_from_time=None
        )

    assert group_payloads == [{"stub": True}, {"stub": True}]
