from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.models import VisitStatus


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    work_start: time
    work_end: time
    latitude: float
    longitude: float


class ServiceVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    address: str
    latitude: float
    longitude: float
    duration_minutes: int
    requested_date: date
    status: VisitStatus


class AssignmentCreate(BaseModel):
    service_visit_id: int
    employee_id: int
    planned_start: datetime


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_visit_id: int
    employee_id: int
    planned_start: datetime
    planned_end: datetime
    employee: EmployeeOut
    service_visit: ServiceVisitOut
