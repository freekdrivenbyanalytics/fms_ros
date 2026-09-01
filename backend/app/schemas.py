from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models import DayType, LunchType, VisitStatus


class GeoPoint(BaseModel):
    lat: float
    lng: float


def _validate_geo_shape(geo_shape: list[GeoPoint] | None) -> list[GeoPoint] | None:
    if geo_shape is not None and len(geo_shape) < 3:
        raise ValueError("geo_shape must have at least 3 coordinate pairs")
    return geo_shape


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    geo_shape: list[GeoPoint] | None = None


class RegionCreate(BaseModel):
    name: str
    geo_shape: list[GeoPoint] | None = None

    @field_validator("geo_shape")
    @classmethod
    def _check_geo_shape(cls, value: list[GeoPoint] | None) -> list[GeoPoint] | None:
        return _validate_geo_shape(value)


class RegionUpdate(BaseModel):
    name: str
    geo_shape: list[GeoPoint] | None = None

    @field_validator("geo_shape")
    @classmethod
    def _check_geo_shape(cls, value: list[GeoPoint] | None) -> list[GeoPoint] | None:
        return _validate_geo_shape(value)


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int | None = None
    url: str | None = None
    name: str
    organization_number: str | None = None
    global_location_number: int | None = None
    supplier_number: int | None = None
    customer_number: int | None = None
    is_supplier: bool | None = None
    is_customer: bool | None = None
    is_inactive: bool | None = None
    email: str | None = None
    invoice_email: str | None = None
    overdue_notice_email: str | None = None
    phone_number: str | None = None
    phone_number_mobile: str | None = None
    description: str | None = None
    language: str | None = None
    display_name: str | None = None
    is_private_individual: bool | None = None
    single_customer_invoice: bool | None = None
    invoice_send_method: str | None = None
    email_attachment_type: str | None = None
    invoices_due_in: int | None = None
    invoices_due_in_type: str | None = None
    is_factoring: bool | None = None
    invoice_send_sms_notification: bool | None = None
    invoice_sms_notification_number: str | None = None
    is_automatic_soft_reminder_enabled: bool | None = None
    is_automatic_reminder_enabled: bool | None = None
    is_automatic_notice_of_debt_collection_enabled: bool | None = None
    discount_percentage: float | None = None
    website: str | None = None
    account_manager: dict | None = None
    department: dict | None = None
    postal_address: dict | None = None
    physical_address: dict | None = None
    delivery_address: dict | None = None
    category1: dict | None = None
    category2: dict | None = None
    category3: dict | None = None
    currency: dict | None = None
    ledger_account: dict | None = None
    bank_account_presentation: list | None = None


class CustomerLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int | None = None
    url: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: dict | None = None
    name: str | None = None
    address: str
    latitude: float | None = None
    longitude: float | None = None
    customer: CustomerOut
    region: RegionOut | None = None


class ContractLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    start_date: date
    end_date: date | None = None
    interval_days: int
    duration_minutes: int
    customer_location: CustomerLocationOut
    required_skills: list[SkillOut]


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer: CustomerOut
    lines: list[ContractLineOut]


class ContractCreate(BaseModel):
    customer_id: int


class ContractUpdate(BaseModel):
    customer_id: int


class ContractLineCreate(BaseModel):
    customer_location_id: int
    start_date: date
    end_date: date | None = None
    interval_days: int
    duration_minutes: int
    required_skill_ids: list[int]


class ContractLineUpdate(BaseModel):
    customer_location_id: int
    start_date: date
    end_date: date | None = None
    interval_days: int
    duration_minutes: int
    required_skill_ids: list[int]


class EmployeeScheduleTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    start_date: date
    end_date: date | None = None
    work_start: time
    work_end: time
    max_hours_per_day: float
    lunch_type: LunchType
    lunch_start: time | None = None
    lunch_end: time | None = None
    lunch_duration_minutes: int | None = None


class EmployeeScheduleTemplateCreate(BaseModel):
    start_date: date
    end_date: date | None = None
    work_start: time
    work_end: time
    max_hours_per_day: float
    lunch_type: LunchType = LunchType.NONE
    lunch_start: time | None = None
    lunch_end: time | None = None
    lunch_duration_minutes: int | None = None


class EmployeeScheduleTemplateUpdate(BaseModel):
    start_date: date
    end_date: date | None = None
    work_start: time
    work_end: time
    max_hours_per_day: float
    lunch_type: LunchType = LunchType.NONE
    lunch_start: time | None = None
    lunch_end: time | None = None
    lunch_duration_minutes: int | None = None


class EmployeeScheduleDayOverrideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    date: date
    day_type: DayType
    work_start: time | None = None
    work_end: time | None = None
    max_hours_per_day: float | None = None
    overtime_minutes: int | None = None


class EmployeeScheduleDayOverrideCreate(BaseModel):
    date: date
    day_type: DayType
    work_start: time | None = None
    work_end: time | None = None
    max_hours_per_day: float | None = None
    overtime_minutes: int | None = None


class EmployeeScheduleDayOverrideUpdate(BaseModel):
    day_type: DayType
    work_start: time | None = None
    work_end: time | None = None
    max_hours_per_day: float | None = None
    overtime_minutes: int | None = None


class EmployeeScheduleDayOverrideBulkCreate(BaseModel):
    start_date: date
    end_date: date
    day_type: DayType


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    latitude: float
    longitude: float
    regions: list[RegionOut]
    skills: list[SkillOut]
    schedule_templates: list[EmployeeScheduleTemplateOut]
    schedule_overrides: list[EmployeeScheduleDayOverrideOut]


class EmployeeCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    region_ids: list[int]
    skill_ids: list[int] = []


class EmployeeUpdate(BaseModel):
    name: str
    latitude: float
    longitude: float
    region_ids: list[int]
    skill_ids: list[int] = []


class ServiceVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requested_date: date
    status: VisitStatus
    contract_line: ContractLineOut


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
    pinned: bool
    employee: EmployeeOut
    service_visit: ServiceVisitOut

    @model_validator(mode="after")
    def _lock_if_started(self) -> "AssignmentOut":
        if self.planned_start <= datetime.now():
            self.pinned = True
        return self


class AssignmentPinUpdate(BaseModel):
    pinned: bool


class ProposedAssignmentOut(BaseModel):
    service_visit_id: int
    employee_id: int
    planned_start: datetime
    planned_end: datetime
    employee: EmployeeOut
    service_visit: ServiceVisitOut


class OptimizationProposal(BaseModel):
    scheduled: list[ProposedAssignmentOut]
    unscheduled_visit_ids: list[int]


class OptimizationApplyRequest(BaseModel):
    scheduled: list[AssignmentCreate]


class OptimizationApplyResult(BaseModel):
    created: list[AssignmentOut]
    skipped_visit_ids: list[int]
