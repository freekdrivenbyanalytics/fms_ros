import enum
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Column,
    Computed,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VisitStatus(str, enum.Enum):
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"


employee_regions = Table(
    "employee_regions",
    Base.metadata,
    Column("employee_id", ForeignKey("employees.id"), primary_key=True),
    Column("region_id", ForeignKey("regions.id"), primary_key=True),
)

contract_line_products = Table(
    "contract_line_products",
    Base.metadata,
    Column("contract_line_id", ForeignKey("contract_lines.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)

product_skills = Table(
    "product_skills",
    Base.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)

employee_skills = Table(
    "employee_skills",
    Base.metadata,
    Column("employee_id", ForeignKey("employees.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    products: Mapped[list["Product"]] = relationship(
        secondary=product_skills, back_populates="skills"
    )
    employees: Mapped[list["Employee"]] = relationship(
        secondary=employee_skills, back_populates="skills"
    )


class ServiceOrderType(Base):
    __tablename__ = "service_order_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    products: Mapped[list["Product"]] = relationship(back_populates="service_order_type")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    geo_shape: Mapped[list | None] = mapped_column(JSONB)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    employees: Mapped[list["Employee"]] = relationship(
        secondary=employee_regions, back_populates="regions"
    )
    customer_locations: Mapped[list["CustomerLocation"]] = relationship(
        back_populates="region"
    )


class LocationKind(str, enum.Enum):
    CUSTOMER_LOCATION = "customer_location"
    EMPLOYEE = "employee"


_location_kind_enum = Enum(
    LocationKind,
    name="location_kind",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class DrivingTime(Base):
    """A single, static driving time (minutes) from one region location
    endpoint to another, sourced from TomTom. origin/destination are
    (kind, id) pairs since they may reference either a CustomerLocation or
    an Employee's home location - two separate id spaces. See
    app.tomtom_routing."""

    __tablename__ = "driving_times"
    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "origin_kind",
            "origin_id",
            "destination_kind",
            "destination_id",
            name="uq_driving_times_region_pair",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"), nullable=False
    )
    origin_kind: Mapped[LocationKind] = mapped_column(_location_kind_enum, nullable=False)
    origin_id: Mapped[int] = mapped_column(Integer, nullable=False)
    destination_kind: Mapped[LocationKind] = mapped_column(_location_kind_enum, nullable=False)
    destination_id: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    region: Mapped["Region"] = relationship()


class ProductChangeType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"


class Product(Base):
    __tablename__ = "products"

    # fms_ros-assigned - fms_ros is the system of record. tripletex_id below
    # is a remembered external reference, set once the product has been
    # pushed to Tripletex; never used as this table's key.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Local-only fields, not sourced from or written back to Tripletex.
    archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tripletex_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    resco_product_id: Mapped[str | None] = mapped_column(String)
    # "TJN" (tjeneste/service) or "PRD" (produkt/product) — always derived from
    # number's actual prefix, never trusted as independently authoritative.
    product_type: Mapped[str] = mapped_column(
        String, nullable=False, default="TJN", server_default="TJN"
    )
    service_order_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_order_types.id")
    )

    skills: Mapped[list["Skill"]] = relationship(
        secondary=product_skills, back_populates="products"
    )
    service_order_type: Mapped["ServiceOrderType | None"] = relationship(
        back_populates="products"
    )
    contract_lines: Mapped[list["ContractLine"]] = relationship(
        secondary=contract_line_products, back_populates="required_products"
    )


class ProductSyncLog(Base):
    __tablename__ = "product_sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    change_type: Mapped[ProductChangeType] = mapped_column(
        Enum(
            ProductChangeType,
            name="product_change_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class CustomerChangeType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"


class Customer(Base):
    __tablename__ = "customers"

    # fms_ros-assigned - fms_ros is the system of record. tripletex_id below
    # is a remembered external reference, set once the customer has been
    # pushed to Tripletex; never used as this table's key.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, nullable=False)
    organization_number: Mapped[str | None] = mapped_column(String)
    global_location_number: Mapped[int | None] = mapped_column(Integer)
    supplier_number: Mapped[int | None] = mapped_column(Integer)
    customer_number: Mapped[int | None] = mapped_column(Integer)
    is_supplier: Mapped[bool | None] = mapped_column(Boolean)
    is_customer: Mapped[bool | None] = mapped_column(Boolean)
    is_inactive: Mapped[bool | None] = mapped_column(Boolean)
    email: Mapped[str | None] = mapped_column(String)
    invoice_email: Mapped[str | None] = mapped_column(String)
    overdue_notice_email: Mapped[str | None] = mapped_column(String)
    phone_number: Mapped[str | None] = mapped_column(String)
    phone_number_mobile: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String)
    display_name: Mapped[str | None] = mapped_column(String)
    is_private_individual: Mapped[bool | None] = mapped_column(Boolean)
    single_customer_invoice: Mapped[bool | None] = mapped_column(Boolean)
    invoice_send_method: Mapped[str | None] = mapped_column(String)
    email_attachment_type: Mapped[str | None] = mapped_column(String)
    invoices_due_in: Mapped[int | None] = mapped_column(Integer)
    invoices_due_in_type: Mapped[str | None] = mapped_column(String)
    is_factoring: Mapped[bool | None] = mapped_column(Boolean)
    invoice_send_sms_notification: Mapped[bool | None] = mapped_column(Boolean)
    invoice_sms_notification_number: Mapped[str | None] = mapped_column(String)
    is_automatic_soft_reminder_enabled: Mapped[bool | None] = mapped_column(Boolean)
    is_automatic_reminder_enabled: Mapped[bool | None] = mapped_column(Boolean)
    is_automatic_notice_of_debt_collection_enabled: Mapped[bool | None] = mapped_column(
        Boolean
    )
    discount_percentage: Mapped[float | None] = mapped_column(Float)
    website: Mapped[str | None] = mapped_column(String)

    # Nested/list-valued Tripletex fields, stored as-is.
    account_manager: Mapped[dict | None] = mapped_column(JSONB)
    department: Mapped[dict | None] = mapped_column(JSONB)
    postal_address: Mapped[dict | None] = mapped_column(JSONB)
    physical_address: Mapped[dict | None] = mapped_column(JSONB)
    delivery_address: Mapped[dict | None] = mapped_column(JSONB)
    category1: Mapped[dict | None] = mapped_column(JSONB)
    category2: Mapped[dict | None] = mapped_column(JSONB)
    category3: Mapped[dict | None] = mapped_column(JSONB)
    currency: Mapped[dict | None] = mapped_column(JSONB)
    ledger_account: Mapped[dict | None] = mapped_column(JSONB)
    bank_account_presentation: Mapped[list | None] = mapped_column(JSONB)

    # Local sync bookkeeping, not sourced from Tripletex.
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Locally-managed soft-delete, independent of Tripletex sync (see
    # add-master-data-crud design.md for why this must be separate from
    # delete_flag).
    archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    tripletex_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    resco_account_id: Mapped[str | None] = mapped_column(String)

    locations: Mapped[list["CustomerLocation"]] = relationship(
        back_populates="customer"
    )
    contracts: Mapped[list["Contract"]] = relationship(back_populates="customer")


class CustomerSyncLog(Base):
    __tablename__ = "customer_sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    change_type: Mapped[CustomerChangeType] = mapped_column(
        Enum(
            CustomerChangeType,
            name="customer_change_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class CustomerLocationChangeType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"


class CustomerLocation(Base):
    __tablename__ = "customer_locations"

    # fms_ros-assigned - fms_ros is the system of record. tripletex_id below
    # is a remembered external reference, set once the location has been
    # pushed to Tripletex; never used as this table's key.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(String)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    address_line_1: Mapped[str | None] = mapped_column(String)
    address_line_2: Mapped[str | None] = mapped_column(String)
    postal_code: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    country: Mapped[dict | None] = mapped_column(JSONB)
    name: Mapped[str | None] = mapped_column(String)
    address: Mapped[str] = mapped_column(String, nullable=False)

    # Local fields. region is assigned via on-demand geofencing (see
    # app.geofencing), not by Tripletex sync; coordinates are geocoded
    # locally since Tripletex doesn't provide them, unless locked.
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    coordinates_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Locally-managed soft-delete, independent of Tripletex sync (see
    # add-master-data-crud design.md for why this must be separate from
    # delete_flag).
    archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tripletex_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    resco_asset_id: Mapped[str | None] = mapped_column(String)

    customer: Mapped["Customer"] = relationship(back_populates="locations")
    region: Mapped["Region | None"] = relationship(back_populates="customer_locations")
    contract_lines: Mapped[list["ContractLine"]] = relationship(
        back_populates="customer_location"
    )


class CustomerLocationSyncLog(Base):
    __tablename__ = "customer_location_sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_location_id: Mapped[int] = mapped_column(
        ForeignKey("customer_locations.id"), nullable=False
    )
    change_type: Mapped[CustomerLocationChangeType] = mapped_column(
        Enum(
            CustomerLocationChangeType,
            name="customer_location_change_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    customer: Mapped["Customer"] = relationship(back_populates="contracts")
    lines: Mapped[list["ContractLine"]] = relationship(back_populates="contract")


class ContractLine(Base):
    __tablename__ = "contract_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    customer_location_id: Mapped[int] = mapped_column(
        ForeignKey("customer_locations.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    # "week", "month", or "quarter" — see schemas.ALLOWED_CONTRACT_LINE_INTERVALS
    # for the fixed set of (interval_unit, interval_count) pairs this may take.
    interval_unit: Mapped[str] = mapped_column(String, nullable=False)
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default="2")
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    contract: Mapped["Contract"] = relationship(back_populates="lines")
    customer_location: Mapped["CustomerLocation"] = relationship(
        back_populates="contract_lines"
    )
    required_products: Mapped[list["Product"]] = relationship(
        secondary=contract_line_products, back_populates="contract_lines"
    )
    service_visits: Mapped[list["ServiceVisit"]] = relationship(
        back_populates="contract_line"
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(
        String, Computed("first_name || ' ' || last_name", persisted=True)
    )
    email: Mapped[str | None] = mapped_column(String)
    mobile_phone: Mapped[str | None] = mapped_column(String)
    resco_user_id: Mapped[str | None] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    regions: Mapped[list["Region"]] = relationship(
        secondary=employee_regions, back_populates="employees"
    )
    skills: Mapped[list["Skill"]] = relationship(
        secondary=employee_skills, back_populates="employees"
    )
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="employee")
    schedule_templates: Mapped[list["EmployeeScheduleTemplate"]] = relationship(
        back_populates="employee"
    )
    schedule_overrides: Mapped[list["EmployeeScheduleDayOverride"]] = relationship(
        back_populates="employee"
    )


class LunchType(str, enum.Enum):
    NONE = "none"
    FIXED = "fixed"
    FLEXIBLE = "flexible"


class DayType(str, enum.Enum):
    WORKING = "working"
    HOLIDAY = "holiday"
    SICK = "sick"


class EmployeeScheduleTemplate(Base):
    __tablename__ = "employee_schedule_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    work_start: Mapped[time] = mapped_column(Time, nullable=False)
    work_end: Mapped[time] = mapped_column(Time, nullable=False)
    max_hours_per_day: Mapped[float] = mapped_column(Float, nullable=False)
    lunch_type: Mapped[LunchType] = mapped_column(
        Enum(
            LunchType,
            name="lunch_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=LunchType.NONE,
        server_default=LunchType.NONE.value,
    )
    lunch_start: Mapped[time | None] = mapped_column(Time)
    lunch_end: Mapped[time | None] = mapped_column(Time)
    lunch_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    employee: Mapped["Employee"] = relationship(back_populates="schedule_templates")


class EmployeeScheduleDayOverride(Base):
    __tablename__ = "employee_schedule_day_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    day_type: Mapped[DayType] = mapped_column(
        Enum(
            DayType,
            name="day_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    work_start: Mapped[time | None] = mapped_column(Time)
    work_end: Mapped[time | None] = mapped_column(Time)
    max_hours_per_day: Mapped[float | None] = mapped_column(Float)
    overtime_minutes: Mapped[int | None] = mapped_column(Integer)
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    employee: Mapped["Employee"] = relationship(back_populates="schedule_overrides")


class ServiceVisit(Base):
    __tablename__ = "service_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_line_id: Mapped[int] = mapped_column(
        ForeignKey("contract_lines.id"), nullable=False
    )
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[VisitStatus] = mapped_column(
        Enum(
            VisitStatus,
            name="visit_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=VisitStatus.UNASSIGNED,
        server_default=VisitStatus.UNASSIGNED.value,
    )

    contract_line: Mapped["ContractLine"] = relationship(back_populates="service_visits")
    assignment: Mapped["Assignment | None"] = relationship(
        back_populates="service_visit", uselist=False
    )


class Assignment(Base):
    __tablename__ = "assignments"

    service_visit_id: Mapped[int] = mapped_column(
        ForeignKey("service_visits.id"), primary_key=True
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    planned_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    planned_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    resco_work_order_id: Mapped[str | None] = mapped_column(String)
    resco_work_order_schedule_id: Mapped[str | None] = mapped_column(String)

    service_visit: Mapped["ServiceVisit"] = relationship(back_populates="assignment")
    employee: Mapped["Employee"] = relationship(back_populates="assignments")


user_customers = Table(
    "user_customers",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("customer_id", ForeignKey("customers.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    delete_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    customers: Mapped[list["Customer"]] = relationship(secondary=user_customers)


class ServiceRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    customer_location_id: Mapped[int] = mapped_column(
        ForeignKey("customer_locations.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(String)
    status: Mapped[ServiceRequestStatus] = mapped_column(
        Enum(
            ServiceRequestStatus,
            name="service_request_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ServiceRequestStatus.PENDING,
        server_default=ServiceRequestStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    customer: Mapped["Customer"] = relationship()
    customer_location: Mapped["CustomerLocation"] = relationship()
    product: Mapped["Product"] = relationship()
