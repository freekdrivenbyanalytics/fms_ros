from app.solver_client import apply_plan_from_floor


def test_no_floor_leaves_window_unchanged() -> None:
    assert apply_plan_from_floor(480, 960, is_today=True, plan_from_minutes=None) == (480, 960)


def test_floor_not_applied_to_other_days() -> None:
    # A plan_from_minutes later than the resolved start would normally push
    # it later, but is_today=False means this isn't today's entry.
    assert apply_plan_from_floor(480, 960, is_today=False, plan_from_minutes=600) == (480, 960)


def test_later_floor_pushes_start_later_today() -> None:
    assert apply_plan_from_floor(480, 960, is_today=True, plan_from_minutes=600) == (600, 960)


def test_earlier_floor_never_moves_start_earlier() -> None:
    # Employee's normal start (540) is already later than the floor (480) -
    # the floor must never pull it earlier than their normal start.
    assert apply_plan_from_floor(540, 960, is_today=True, plan_from_minutes=480) == (540, 960)


def test_floor_at_or_past_end_omits_the_entry() -> None:
    assert apply_plan_from_floor(480, 600, is_today=True, plan_from_minutes=600) is None
    assert apply_plan_from_floor(480, 600, is_today=True, plan_from_minutes=700) is None
