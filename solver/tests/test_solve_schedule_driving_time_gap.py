from app.schemas import (
    DrivingTimeIn,
    EmployeeDayScheduleIn,
    EmployeeIn,
    OptimizeRequest,
    VisitIn,
)
from app.solve import solve_schedule

DAY = "2026-01-05"


def test_proposed_gap_respects_driving_time_or_leaves_a_visit_unscheduled() -> None:
    # One employee, one full working day, two visits at different locations
    # 60 minutes apart by road. With plenty of working hours available, the
    # solver should be able to fit both while leaving at least a 60-minute
    # gap between them - the bug this change fixes was proposing them
    # back-to-back regardless of driving time.
    request = OptimizeRequest(
        employees=[
            EmployeeIn(id=1, employee_skill_ids=[], region_ids=[1], latitude=52.0, longitude=5.0)
        ],
        employee_day_schedules=[
            EmployeeDayScheduleIn(employee_id=1, date=DAY, start_minutes=480, end_minutes=1200)
        ],
        visits=[
            VisitIn(
                id=1,
                requested_date=DAY,
                duration_minutes=60,
                required_skill_ids=[],
                region_id=1,
                location_id=100,
                latitude=52.0,
                longitude=5.0,
                priority=2,
                days_until_due=0,
            ),
            VisitIn(
                id=2,
                requested_date=DAY,
                duration_minutes=60,
                required_skill_ids=[],
                region_id=1,
                location_id=200,
                latitude=52.2,
                longitude=5.2,
                priority=2,
                days_until_due=0,
            ),
        ],
        driving_times=[
            DrivingTimeIn(
                origin_kind="employee",
                origin_id=1,
                destination_kind="customer_location",
                destination_id=100,
                duration_minutes=10,
            ),
            DrivingTimeIn(
                origin_kind="employee",
                origin_id=1,
                destination_kind="customer_location",
                destination_id=200,
                duration_minutes=10,
            ),
            DrivingTimeIn(
                origin_kind="customer_location",
                origin_id=100,
                destination_kind="customer_location",
                destination_id=200,
                duration_minutes=60,
            ),
            DrivingTimeIn(
                origin_kind="customer_location",
                origin_id=200,
                destination_kind="customer_location",
                destination_id=100,
                duration_minutes=60,
            ),
        ],
        time_limit_seconds=5,
    )

    response = solve_schedule(request)

    scheduled_by_visit = {item.visit_id: item for item in response.scheduled}

    if 1 in scheduled_by_visit and 2 in scheduled_by_visit:
        first, second = sorted(
            (scheduled_by_visit[1], scheduled_by_visit[2]), key=lambda item: item.start_minutes
        )
        gap = second.start_minutes - first.end_minutes
        assert gap >= 60, (
            f"Expected at least 60 minutes between visits given the driving time, got {gap}"
        )
    else:
        # Leaving one unscheduled is an acceptable outcome of the hard
        # constraint too, as long as the solver didn't cheat the gap.
        assert set(response.unscheduled_visit_ids) & {1, 2}
