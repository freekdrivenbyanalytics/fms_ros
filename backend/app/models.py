import enum
from datetime import date, datetime, time

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
)
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


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(
        secondary=employee_regions, back_populates="regions"
    )
    customer_locations: Mapped[list["CustomerLocation"]] = relationship(
        back_populates="region"
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    locations: Mapped[list["CustomerLocation"]] = relationship(
        back_populates="customer"
    )


class CustomerLocation(Base):
    __tablename__ = "customer_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="locations")
    region: Mapped["Region"] = relationship(back_populates="customer_locations")
    service_visits: Mapped[list["ServiceVisit"]] = relationship(
        back_populates="customer_location"
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    work_start: Mapped[time] = mapped_column(Time, nullable=False)
    work_end: Mapped[time] = mapped_column(Time, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    regions: Mapped[list["Region"]] = relationship(
        secondary=employee_regions, back_populates="employees"
    )
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="employee")


class ServiceVisit(Base):
    __tablename__ = "service_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_location_id: Mapped[int] = mapped_column(
        ForeignKey("customer_locations.id"), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
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

    customer_location: Mapped["CustomerLocation"] = relationship(
        back_populates="service_visits"
    )
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

    service_visit: Mapped["ServiceVisit"] = relationship(back_populates="assignment")
    employee: Mapped["Employee"] = relationship(back_populates="assignments")
