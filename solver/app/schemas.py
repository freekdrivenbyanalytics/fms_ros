from datetime import date

from pydantic import BaseModel

DEFAULT_TIME_LIMIT_SECONDS = 30


class EmployeeIn(BaseModel):
    id: int
    skill_ids: list[int]
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
    latitude: float
    longitude: float


class ExistingAssignmentIn(BaseModel):
    id: str
    employee_id: int
    requested_date: date
    start_minutes: int
    end_minutes: int
    latitude: float
    longitude: float


class OptimizeRequest(BaseModel):
    employees: list[EmployeeIn]
    employee_day_schedules: list[EmployeeDayScheduleIn] = []
    visits: list[VisitIn]
    existing_assignments: list[ExistingAssignmentIn] = []
    time_limit_seconds: int | None = None


class ScheduledVisitOut(BaseModel):
    visit_id: int
    employee_id: int
    start_minutes: int
    end_minutes: int


class OptimizeResponse(BaseModel):
    scheduled: list[ScheduledVisitOut]
    unscheduled_visit_ids: list[int]
