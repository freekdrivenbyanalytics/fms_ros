from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models import DayType, LocationKind, LunchType, ServiceRequestStatus, VisitStatus


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


class SkillCreate(BaseModel):
    name: str


class SkillUpdate(BaseModel):
    name: str


class ServiceOrderTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ServiceOrderTypeCreate(BaseModel):
    name: str


class ServiceOrderTypeUpdate(BaseModel):
    name: str


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    product_type: str
    name: str
    tripletex_id: int | None = None
    resco_product_id: str | None = None
    # Transient - only set on the specific create/update response that just
    # attempted a Tripletex/Resco push and had it (partly) fail. Never
    # persisted, never present on a plain GET.
    sync_warning: str | None = None
    skills: list[SkillOut] = []
    service_order_type: ServiceOrderTypeOut | None = None


class ProductCreate(BaseModel):
    product_type: Literal["TJN", "PRD"]
    number: str
    name: str
    skill_ids: list[int] = []
    service_order_type_id: int | None = None


class ProductUpdate(BaseModel):
    product_type: Literal["TJN", "PRD"]
    number: str
    name: str
    skill_ids: list[int] = []
    service_order_type_id: int | None = None


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
    tripletex_id: int | None = None
    resco_account_id: str | None = None
    resco_contact_id: str | None = None
    contact_name: str | None = None
    # Transient - only set on the specific create/update response that just
    # attempted a Tripletex/Resco push and had it (partly) fail. Never
    # persisted, never present on a plain GET.
    sync_warning: str | None = None


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
    coordinates_locked: bool = False
    tripletex_id: int | None = None
    resco_asset_id: str | None = None
    resco_functional_location_id: str | None = None
    sync_warning: str | None = None
    customer: CustomerOut
    region: RegionOut | None = None


class CustomerLocationCoordinatesUpdate(BaseModel):
    latitude: float
    longitude: float
    coordinates_locked: bool


class CustomerCreate(BaseModel):
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    phone_number_mobile: str | None = None
    organization_number: str | None = None


class CustomerUpdate(BaseModel):
    name: str
    contact_name: str | None = None
    phone_number_mobile: str | None = None
    email: str | None = None
    phone_number: str | None = None
    organization_number: str | None = None


class CustomerLocationCreate(BaseModel):
    customer_id: int
    address_line_1: str
    address_line_2: str | None = None
    postal_code: str | None = None
    city: str | None = None


class CustomerLocationUpdate(BaseModel):
    address_line_1: str
    address_line_2: str | None = None
    postal_code: str | None = None
    city: str | None = None


ALLOWED_CONTRACT_LINE_INTERVALS: set[tuple[str, int]] = {
    ("week", 1),
    ("week", 2),
    ("week", 3),
    ("week", 4),
    ("month", 1),
    ("month", 2),
    ("month", 3),
    ("quarter", 1),
}


def _validate_contract_line_interval(
    interval_unit: str, interval_count: int
) -> None:
    if (interval_unit, interval_count) not in ALLOWED_CONTRACT_LINE_INTERVALS:
        raise ValueError(
            f"Unsupported interval: every {interval_count} {interval_unit}(s). "
            f"Allowed combinations: {sorted(ALLOWED_CONTRACT_LINE_INTERVALS)}"
        )


class ContractLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    start_date: date
    end_date: date | None = None
    interval_unit: Literal["week", "month", "quarter"]
    interval_count: int
    duration_minutes: int
    priority: int
    customer_location: CustomerLocationOut
    required_products: list[ProductOut]


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
    interval_unit: Literal["week", "month", "quarter"]
    interval_count: int
    duration_minutes: int
    priority: int = 2
    required_product_ids: list[int]

    @model_validator(mode="after")
    def _check_interval(self) -> "ContractLineCreate":
        _validate_contract_line_interval(self.interval_unit, self.interval_count)
        return self


class ContractLineUpdate(BaseModel):
    customer_location_id: int
    start_date: date
    end_date: date | None = None
    interval_unit: Literal["week", "month", "quarter"]
    interval_count: int
    duration_minutes: int
    priority: int = 2
    required_product_ids: list[int]

    @model_validator(mode="after")
    def _check_interval(self) -> "ContractLineUpdate":
        _validate_contract_line_interval(self.interval_unit, self.interval_count)
        return self


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


class EmployeeRescoSyncResult(BaseModel):
    status: Literal["synced", "skipped", "failed"]
    detail: str | None = None


class CustomerRescoSyncResult(BaseModel):
    status: Literal["synced", "skipped", "failed"]
    detail: str | None = None


class CustomerLocationRescoSyncResult(BaseModel):
    status: Literal["synced", "skipped", "failed"]
    detail: str | None = None


class ProductRescoSyncResult(BaseModel):
    status: Literal["synced", "skipped", "failed"]
    detail: str | None = None


class AssignmentRescoSyncResult(BaseModel):
    status: Literal["synced", "skipped", "failed"]
    detail: str | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    name: str
    email: str | None = None
    mobile_phone: str | None = None
    latitude: float
    longitude: float
    regions: list[RegionOut]
    skills: list[SkillOut]
    schedule_templates: list[EmployeeScheduleTemplateOut]
    schedule_overrides: list[EmployeeScheduleDayOverrideOut]
    resco_sync: EmployeeRescoSyncResult | None = None


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    mobile_phone: str | None = None
    latitude: float
    longitude: float
    region_ids: list[int]
    skill_ids: list[int] = []


class EmployeeUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    mobile_phone: str | None = None
    latitude: float
    longitude: float
    region_ids: list[int]
    skill_ids: list[int] = []


class RescoSyncSummary(BaseModel):
    created: int
    updated: int
    skipped: int
    failed: int
    errors: list[str] = []


class ServiceVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requested_date: date
    status: VisitStatus
    unassigned_reason: str | None = None
    contract_line: ContractLineOut
    required_skills: list[SkillOut] = []

    @model_validator(mode="after")
    def _compute_required_skills(self) -> "ServiceVisitOut":
        seen: dict[int, SkillOut] = {}
        for product in self.contract_line.required_products:
            for skill in product.skills:
                seen[skill.id] = skill
        self.required_skills = list(seen.values())
        return self


class AssignmentCreate(BaseModel):
    service_visit_id: int
    employee_id: int
    planned_start: datetime


class FreeSlotOut(BaseModel):
    employee_id: int
    employee_name: str
    start: datetime
    end: datetime


class AdHocVisitCreate(BaseModel):
    employee_id: int
    start: datetime


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_visit_id: int
    employee_id: int
    planned_start: datetime
    planned_end: datetime
    pinned: bool
    employee: EmployeeOut
    service_visit: ServiceVisitOut
    resco_sync: AssignmentRescoSyncResult | None = None
    resco_work_order_id: str | None = None
    resco_work_order_schedule_id: str | None = None
    resco_status: str | None = None
    resco_statecode: int | None = None
    resco_statuscode: int | None = None

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


class OptimizeRunOptions(BaseModel):
    days_ahead: int = 2
    time_limit_seconds: int | None = None
    execution_mode: Literal["single", "parallel"] = "single"
    # "HH:MM"; no visit is proposed to start earlier than this today. Does
    # not affect any other date in the run's scheduling window.
    plan_from_time: str | None = None


class OptimizationProposal(BaseModel):
    scheduled: list[ProposedAssignmentOut]
    unscheduled_visit_ids: list[int]


class OptimizationApplyRequest(BaseModel):
    scheduled: list[AssignmentCreate]


class OptimizationApplyResult(BaseModel):
    created: list[AssignmentOut]
    skipped_visit_ids: list[int]


class DrivingTimeComputeSummary(BaseModel):
    computed: int
    skipped: int


class ContractLineExtendSummary(BaseModel):
    lines_extended: int
    visits_created: int


class DayPlanningStopOut(BaseModel):
    kind: LocationKind
    latitude: float
    longitude: float
    service_visit_id: int | None = None
    customer_name: str | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None


class DayPlanningEmployeeRouteOut(BaseModel):
    employee_id: int
    employee_name: str
    stops: list[DayPlanningStopOut]
    route: list[GeoPoint]


class DayPlanningRoutesOut(BaseModel):
    employees: list[DayPlanningEmployeeRouteOut]


class DemoScheduleRefreshSummary(BaseModel):
    days_shifted: int
    visits_unassigned: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_admin: bool
    customer_ids: list[int]


class CurrentUserOut(BaseModel):
    id: int
    email: str
    is_admin: bool
    customer_ids: list[int]


class UserCreate(BaseModel):
    email: str
    password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserCustomersUpdate(BaseModel):
    customer_ids: list[int]


class UserAdminUpdate(BaseModel):
    is_admin: bool


class UserPasswordReset(BaseModel):
    password: str


class ServiceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer: CustomerOut
    customer_location: CustomerLocationOut
    product: ProductOut
    note: str | None = None
    status: ServiceRequestStatus
    created_at: datetime


class ServiceRequestCreate(BaseModel):
    customer_id: int
    customer_location_id: int
    product_id: int
    note: str | None = None


class CustomerDashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer: CustomerOut
    customer_locations: list[CustomerLocationOut]
    contracts: list[ContractOut]
    upcoming_visits: list[ServiceVisitOut]


class RescoStatusSyncSummary(BaseModel):
    pulled: int = 0
    skipped: int = 0
    failed: int = 0
    reconciled: int = 0
    reconciliation_skipped: int = 0
    reset_failed: int = 0
    errors: list[str] = []
    skip_reasons: list[str] = []
