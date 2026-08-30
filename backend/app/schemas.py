from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, model_validator

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
