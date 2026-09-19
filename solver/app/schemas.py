from datetime import date

from pydantic import BaseModel

DEFAULT_TIME_LIMIT_SECONDS = 30


class EmployeeIn(BaseModel):
    id: int
    employee_skill_ids: list[int]
    region_ids: list[int]
    latitude: float
    longitude: float


class EmployeeDayScheduleIn(BaseModel):
    employee_id: int
    date: date
    start_minutes: int
    end_minutes: int


class VisitIn(BaseModel):
    id: int
    # Fixed nominal (contract-cadence) date - the preference anchor, not
    # necessarily the date this visit gets scheduled on. See
    # OptimizeRequest.candidate_dates for the actual value range.
    requested_date: date
    duration_minutes: int
    required_skill_ids: list[int]
    region_id: int
    location_id: int
    latitude: float
    longitude: float
    priority: int
    days_until_due: int
    # Nominal days since this visit's contract line's previous occurrence -
    # None if there is no previous occurrence. Paired with at most one of
    # previous_visit_id/previous_actual_date.
    interval_days: int | None = None
    previous_visit_id: int | None = None
    previous_actual_date: date | None = None


class ExistingAssignmentIn(BaseModel):
    id: str
    employee_id: int
    # The date this locked assignment actually occupies (its planned_start's
    # date) - not the visit's nominal requested_date, which can differ once
    # a visit has been rescheduled.
    date: date
    start_minutes: int
    end_minutes: int
    location_id: int
    latitude: float
    longitude: float


class DrivingTimeIn(BaseModel):
    origin_kind: str
    origin_id: int
    destination_kind: str
    destination_id: int
    duration_minutes: int


class OptimizeRequest(BaseModel):
    employees: list[EmployeeIn]
    employee_day_schedules: list[EmployeeDayScheduleIn] = []
    visits: list[VisitIn]
    existing_assignments: list[ExistingAssignmentIn] = []
    driving_times: list[DrivingTimeIn] = []
    # Every date a visit may be scheduled on this run - the `date` planning
    # variable's value range. Required, not defaulted: the caller decides
    # the run's scheduling window, the solver never invents one.
    candidate_dates: list[date]
    time_limit_seconds: int | None = None


class ScheduledVisitOut(BaseModel):
    visit_id: int
    employee_id: int
    date: date
    start_minutes: int
    end_minutes: int


class OptimizeResponse(BaseModel):
    scheduled: list[ScheduledVisitOut]
    unscheduled_visit_ids: list[int]
