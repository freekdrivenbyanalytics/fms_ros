from datetime import date, datetime

from app.solver_client import _NO_PREVIOUS_OCCURRENCE, _compute_previous_occurrences


class _Assignment:
    def __init__(self, planned_start: datetime, pinned: bool = False) -> None:
        self.planned_start = planned_start
        self.pinned = pinned


class _Visit:
    def __init__(
        self,
        id: int,
        contract_line_id: int,
        requested_date: date,
        assignment: _Assignment | None = None,
    ) -> None:
        self.id = id
        self.contract_line_id = contract_line_id
        self.requested_date = requested_date
        self.assignment = assignment


def test_first_occurrence_has_no_previous_occurrence() -> None:
    first = _Visit(1, contract_line_id=1, requested_date=date(2026, 1, 1))

    result = _compute_previous_occurrences([first])

    assert result[first.id] == _NO_PREVIOUS_OCCURRENCE


def test_middle_occurrence_with_schedulable_predecessor_links_by_id() -> None:
    first = _Visit(1, contract_line_id=1, requested_date=date(2026, 1, 1))
    middle = _Visit(2, contract_line_id=1, requested_date=date(2026, 1, 15))
    last = _Visit(3, contract_line_id=1, requested_date=date(2026, 1, 29))

    result = _compute_previous_occurrences([first, middle, last])

    previous_visit_id, previous_actual_date, interval_days = result[middle.id]
    assert previous_visit_id == first.id
    assert previous_actual_date is None
    assert interval_days == 14

    previous_visit_id, previous_actual_date, interval_days = result[last.id]
    assert previous_visit_id == middle.id
    assert previous_actual_date is None
    assert interval_days == 14


def test_predecessor_with_locked_assignment_resolves_to_its_actual_date() -> None:
    # Locked (pinned) even though its own nominal date was 1 Jan - the
    # predecessor's assignment moved it to 3 Jan, and the interval must be
    # measured from that actual date, not the nominal one.
    delayed_first = _Visit(
        1,
        contract_line_id=1,
        requested_date=date(2026, 1, 1),
        assignment=_Assignment(datetime(2026, 1, 3, 9, 0), pinned=True),
    )
    second = _Visit(2, contract_line_id=1, requested_date=date(2026, 1, 15))

    result = _compute_previous_occurrences([delayed_first, second])

    previous_visit_id, previous_actual_date, interval_days = result[second.id]
    assert previous_visit_id is None
    assert previous_actual_date == date(2026, 1, 3)
    # Interval is still nominal-to-nominal (15 - 1 = 14), even though the
    # predecessor's actual date differs - see design.md.
    assert interval_days == 14


def test_unrelated_contract_lines_do_not_link_to_each_other() -> None:
    line_a_visit = _Visit(1, contract_line_id=1, requested_date=date(2026, 1, 1))
    line_b_visit = _Visit(2, contract_line_id=2, requested_date=date(2026, 1, 2))

    result = _compute_previous_occurrences([line_a_visit, line_b_visit])

    assert result[line_a_visit.id] == _NO_PREVIOUS_OCCURRENCE
    assert result[line_b_visit.id] == _NO_PREVIOUS_OCCURRENCE
