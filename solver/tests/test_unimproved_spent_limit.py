from app.solve import _unimproved_spent_limit_seconds


def test_scales_with_time_limit_within_the_floor() -> None:
    assert _unimproved_spent_limit_seconds(30) == 10
    assert _unimproved_spent_limit_seconds(90) == 30
    assert _unimproved_spent_limit_seconds(15) == 5


def test_never_below_the_five_second_floor() -> None:
    assert _unimproved_spent_limit_seconds(1) == 5
    assert _unimproved_spent_limit_seconds(5) == 5
    assert _unimproved_spent_limit_seconds(10) == 5


def test_never_exactly_one_second_regardless_of_time_limit() -> None:
    # The bug this replaces (`min(1, time_limit_seconds)`) always evaluated
    # to exactly 1 second - assert the fix never reproduces that constant.
    for time_limit_seconds in (1, 5, 30, 60, 90, 600):
        assert _unimproved_spent_limit_seconds(time_limit_seconds) != 1
