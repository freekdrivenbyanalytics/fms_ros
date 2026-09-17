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
    requested_date: date
    duration_minutes: int
    required_skill_ids: list[int]
    region_id: int
    location_id: int
    latitude: float
    longitude: float
    priority: int
    days_until_due: int


class ExistingAssignmentIn(BaseModel):
    id: str
    employee_id: int
    requested_date: date
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
    time_limit_seconds: int | None = None


class ScheduledVisitOut(BaseModel):
    visit_id: int
    employee_id: int
    start_minutes: int
    end_minutes: int


class OptimizeResponse(BaseModel):
    scheduled: list[ScheduledVisitOut]
    unscheduled_visit_ids: list[int]
