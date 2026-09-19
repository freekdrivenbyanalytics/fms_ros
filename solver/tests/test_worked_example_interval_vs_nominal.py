from app.schemas import (
    EmployeeDayScheduleIn,
    EmployeeIn,
    ExistingAssignmentIn,
    OptimizeRequest,
    VisitIn,
)
from app.solve import solve_schedule

# Worked example from design.md: a biweekly contract starting 1 Jan. Capacity
# was unavailable on 1 Jan, so visit 1 was locked in on 3 Jan instead. Visit
# 2's nominal (contract-cadence) date is 15 Jan - 14 days after the contract's
# 1 Jan anchor, not 14 days after visit 1's actual 3 Jan date. The interval
# constraint alone would push visit 2 to 18 Jan (a full 14 days after 3 Jan),
# but the nominal-date preference is weighted 10x stronger, so as long as 15
# Jan has capacity the solver should still place visit 2 there.
VISIT_1_ACTUAL_DATE = "2026-01-03"
VISIT_2_NOMINAL_DATE = "2026-01-15"
LATER_CANDIDATE_DATE = "2026-01-18"


def test_nominal_date_wins_over_interval_when_both_dates_have_capacity() -> None:
    request = OptimizeRequest(
        employees=[
            EmployeeIn(id=1, employee_skill_ids=[], region_ids=[1], latitude=52.0, longitude=5.0)
        ],
        employee_day_schedules=[
            EmployeeDayScheduleIn(
                employee_id=1, date=VISIT_2_NOMINAL_DATE, start_minutes=480, end_minutes=1200
            ),
            EmployeeDayScheduleIn(
                employee_id=1, date=LATER_CANDIDATE_DATE, start_minutes=480, end_minutes=1200
            ),
        ],
        visits=[
            VisitIn(
                id=2,
                requested_date=VISIT_2_NOMINAL_DATE,
                duration_minutes=60,
                required_skill_ids=[],
                region_id=1,
                location_id=200,
                latitude=52.0,
                longitude=5.0,
                priority=2,
                days_until_due=0,
                interval_days=14,
                previous_actual_date=VISIT_1_ACTUAL_DATE,
            ),
        ],
        existing_assignments=[
            ExistingAssignmentIn(
                id="visit-1-locked",
                employee_id=1,
                date=VISIT_1_ACTUAL_DATE,
                start_minutes=480,
                end_minutes=540,
                location_id=100,
                latitude=52.0,
                longitude=5.0,
            ),
        ],
        candidate_dates=[VISIT_1_ACTUAL_DATE, VISIT_2_NOMINAL_DATE, LATER_CANDIDATE_DATE],
        time_limit_seconds=5,
    )

    response = solve_schedule(request)

    scheduled_by_visit = {item.visit_id: item for item in response.scheduled}
    assert 2 in scheduled_by_visit
    assert scheduled_by_visit[2].date.isoformat() == VISIT_2_NOMINAL_DATE
