from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.models import VisitStatus


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CustomerLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    latitude: float
    longitude: float
    customer: CustomerOut
    region: RegionOut


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: date
    interval_days: int
    duration_minutes: int
    customer_location: CustomerLocationOut
    required_skills: list[SkillOut]


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    work_start: time
    work_end: time
    latitude: float
    longitude: float
    regions: list[RegionOut]
    skills: list[SkillOut]


class ServiceVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requested_date: date
    status: VisitStatus
    contract: ContractOut


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
