import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta

import httpx
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.ad_hoc_visits import find_free_slots
from app.auth import (
    SESSION_COOKIE_NAME,
    create_session_token,
    customer_scope_ids,
    get_current_user,
    hash_password,
    require_admin,
    require_customer_access,
    require_session,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.demo_schedule_refresh import refresh_demo_schedule
from app.employee_schedule import (
    covering_template,
    effective_max_hours_per_day,
    hours_exceed_cap,
    override_exists_for_date,
    templates_overlap,
)
from app.geocoding import geocode_address
from app.geofencing import assign_regions_by_geofence
from app.tomtom_routing import LocationEndpoint, compute_employee_day_route, compute_region_driving_times
from app.visit_generation import (
    OPEN_ENDED_HORIZON_DAYS,
    extend_occurrence_dates,
    generate_occurrence_dates,
)
from app.models import (
    Assignment,
    Contract,
    ContractLine,
    Customer,
    CustomerLocation,
    DayType,
    Employee,
    EmployeeScheduleDayOverride,
    EmployeeScheduleTemplate,
    LocationKind,
    Product,
    Region,
    ServiceOrderType,
    ServiceRequest,
    ServiceRequestStatus,
    ServiceVisit,
    Skill,
    User,
    VisitStatus,
)
from app.schemas import (
    AdHocVisitCreate,
    AssignmentCreate,
    AssignmentOut,
    AssignmentPinUpdate,
    AssignmentRescoSyncResult,
    ContractCreate,
    ContractLineCreate,
    ContractLineExtendSummary,
    ContractLineOut,
    ContractLineUpdate,
    ContractOut,
    ContractUpdate,
    CustomerCreate,
    CustomerDashboardOut,
    CustomerLocationCoordinatesUpdate,
    CustomerLocationCreate,
    CustomerLocationOut,
    CustomerLocationUpdate,
    CustomerOut,
    CustomerUpdate,
    DayPlanningEmployeeRouteOut,
    DayPlanningRoutesOut,
    DayPlanningStopOut,
    DemoScheduleRefreshSummary,
    DrivingTimeComputeSummary,
    EmployeeCreate,
    EmployeeOut,
    EmployeeRescoSyncResult,
    EmployeeScheduleDayOverrideBulkCreate,
    EmployeeScheduleDayOverrideCreate,
    EmployeeScheduleDayOverrideOut,
    EmployeeScheduleDayOverrideUpdate,
    EmployeeScheduleTemplateCreate,
    EmployeeScheduleTemplateOut,
    EmployeeScheduleTemplateUpdate,
    EmployeeUpdate,
    FreeSlotOut,
    GeoPoint,
    OptimizationApplyRequest,
    OptimizationApplyResult,
    OptimizationProposal,
    OptimizeRunOptions,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProposedAssignmentOut,
    RegionCreate,
    RegionOut,
    RegionUpdate,
    RescoSyncSummary,
    RescoStatusSyncSummary,
    ServiceOrderTypeCreate,
    ServiceOrderTypeOut,
    ServiceOrderTypeUpdate,
    ServiceRequestCreate,
    ServiceRequestOut,
    ServiceVisitOut,
    SkillCreate,
    SkillOut,
    SkillUpdate,
    CurrentUserOut,
    UserAdminUpdate,
    UserCreate,
    UserCustomersUpdate,
    UserLoginRequest,
    UserOut,
    UserPasswordReset,
)
from app.resco import (
    sync_all_employees,
    sync_assignment,
    sync_customer,
    sync_customer_location,
    sync_customer_locations_to_resco,
    sync_assignment_statuses_from_resco,
    sync_customers_to_resco,
    sync_employee,
    sync_product,
)
from app.solver_client import (
    request_parallel_proposals,
    request_proposal,
    resolve_run_payloads,
)
from app.tripletex import (
    TripletexClient,
    sync_customer_locations,
    sync_customers,
    sync_products,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # No Tripletex/Resco sync runs at startup - fms_ros is the system of
    # record for masterdata and doesn't depend on either being reachable.
    # See local-first-masterdata-sync's design.md.
    yield


app = FastAPI(title="fms_ros", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def _employee_out(
    employee: Employee, resco_sync: EmployeeRescoSyncResult | None = None
) -> EmployeeOut:
    return EmployeeOut(
        id=employee.id,
        first_name=employee.first_name,
        last_name=employee.last_name,
        name=employee.name,
        email=employee.email,
        mobile_phone=employee.mobile_phone,
        latitude=employee.latitude,
        longitude=employee.longitude,
        regions=[RegionOut.model_validate(region) for region in employee.regions],
        skills=[SkillOut.model_validate(skill) for skill in employee.skills],
        schedule_templates=[
            EmployeeScheduleTemplateOut.model_validate(template)
            for template in employee.schedule_templates
            if not template.delete_flag
        ],
        schedule_overrides=[
            EmployeeScheduleDayOverrideOut.model_validate(override)
            for override in employee.schedule_overrides
            if not override.delete_flag
        ],
        resco_sync=resco_sync,
    )


def _employee_query(db: Session):
    return db.query(Employee).options(
        joinedload(Employee.regions),
        joinedload(Employee.skills),
        joinedload(Employee.schedule_templates),
        joinedload(Employee.schedule_overrides),
    )


def _lookup_regions_and_skills(
    db: Session, region_ids: list[int], skill_ids: list[int]
) -> tuple[list[Region], list[Skill]]:
    regions = db.query(Region).filter(Region.id.in_(region_ids)).all()
    if len(regions) != len(set(region_ids)):
        raise HTTPException(status_code=404, detail="One or more regions not found")
    skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    if len(skills) != len(set(skill_ids)):
        raise HTTPException(status_code=404, detail="One or more skills not found")
    return regions, skills


def _tripletex_client() -> TripletexClient:
    return TripletexClient(settings.tripletex_base_url, settings.tripletex_session_ttl_seconds)


def _sync_warning(failed_systems: list[str]) -> str | None:
    """A transient warning for a create/update response when a push to
    Tripletex and/or Resco just failed - never persisted, never present on
    a plain GET. The persistent "still needs syncing" signal is the
    relevant *_id field being None, not this."""
    if not failed_systems:
        return None
    return f"Sync to {' and '.join(failed_systems)} failed - retry from Sync to Tripletex."


def _prefixed_product_number(product_type: str, number: str) -> str:
    return number if number.startswith(product_type) else f"{product_type}{number}"


def _lookup_skills(db: Session, skill_ids: list[int]) -> list[Skill]:
    skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    if len(skills) != len(set(skill_ids)):
        raise HTTPException(status_code=404, detail="One or more skills not found")
    return skills


def _validate_service_order_type_id(db: Session, service_order_type_id: int | None) -> None:
    if service_order_type_id is None:
        return
    if db.get(ServiceOrderType, service_order_type_id) is None:
        raise HTTPException(status_code=404, detail="Service order type not found")


def _customer_location_display_address(
    address_line_1: str, postal_code: str | None, city: str | None
) -> str:
    locality = " ".join(part for part in [postal_code, city] if part)
    return ", ".join(part for part in [address_line_1, locality] if part)


@app.get("/employees", response_model=list[EmployeeOut], dependencies=[Depends(require_admin)])
def list_employees(db: Session = Depends(get_db)) -> list[EmployeeOut]:
    employees = (
        _employee_query(db)
        .filter(Employee.delete_flag.is_(False))
        .order_by(Employee.id)
        .all()
    )
    return [_employee_out(employee) for employee in employees]


@app.post("/employees", response_model=EmployeeOut, status_code=201, dependencies=[Depends(require_admin)])
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)) -> EmployeeOut:
    regions, skills = _lookup_regions_and_skills(db, payload.region_ids, payload.skill_ids)

    employee = Employee(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        mobile_phone=payload.mobile_phone,
        latitude=payload.latitude,
        longitude=payload.longitude,
        regions=regions,
        skills=skills,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    try:
        resco_sync = sync_employee(db, employee)
    except Exception:
        logger.warning("Resco sync failed for employee %s", employee.id, exc_info=True)
        resco_sync = EmployeeRescoSyncResult(status="failed", detail="Resco sync failed")

    return _employee_out(employee, resco_sync=resco_sync)


@app.patch("/employees/{employee_id}", response_model=EmployeeOut, dependencies=[Depends(require_admin)])
def update_employee(
    employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)
) -> EmployeeOut:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    regions, skills = _lookup_regions_and_skills(db, payload.region_ids, payload.skill_ids)

    employee.first_name = payload.first_name
    employee.last_name = payload.last_name
    employee.email = payload.email
    employee.mobile_phone = payload.mobile_phone
    employee.latitude = payload.latitude
    employee.longitude = payload.longitude
    employee.regions = regions
    employee.skills = skills
    db.commit()
    db.refresh(employee)

    try:
        resco_sync = sync_employee(db, employee)
    except Exception:
        logger.warning("Resco sync failed for employee %s", employee.id, exc_info=True)
        resco_sync = EmployeeRescoSyncResult(status="failed", detail="Resco sync failed")

    return _employee_out(employee, resco_sync=resco_sync)


@app.post("/employees/sync-resco", response_model=RescoSyncSummary, dependencies=[Depends(require_admin)])
def sync_employees_to_resco(db: Session = Depends(get_db)) -> RescoSyncSummary:
    return sync_all_employees(db)


@app.delete("/employees/{employee_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_employee(employee_id: int, db: Session = Depends(get_db)) -> None:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.delete_flag = True
    db.commit()


def _validate_template_hours(
    db: Session, employee_id: int, payload: EmployeeScheduleTemplateCreate | EmployeeScheduleTemplateUpdate
) -> None:
    if templates_overlap(db, employee_id, payload.start_date, payload.end_date):
        raise HTTPException(
            status_code=422,
            detail="Template date range overlaps an existing template for this employee",
        )
    if hours_exceed_cap(payload.work_start, payload.work_end, payload.max_hours_per_day):
        raise HTTPException(
            status_code=422,
            detail="Template hours exceed its own max hours per day",
        )


@app.get(
    "/employees/{employee_id}/schedule-templates",
    response_model=list[EmployeeScheduleTemplateOut],
    dependencies=[Depends(require_admin)],
)
def list_schedule_templates(
    employee_id: int, db: Session = Depends(get_db)
) -> list[EmployeeScheduleTemplate]:
    return (
        db.query(EmployeeScheduleTemplate)
        .filter(
            EmployeeScheduleTemplate.employee_id == employee_id,
            EmployeeScheduleTemplate.delete_flag.is_(False),
        )
        .order_by(EmployeeScheduleTemplate.start_date)
        .all()
    )


@app.post(
    "/employees/{employee_id}/schedule-templates",
    response_model=EmployeeScheduleTemplateOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_schedule_template(
    employee_id: int,
    payload: EmployeeScheduleTemplateCreate,
    db: Session = Depends(get_db),
) -> EmployeeScheduleTemplate:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    _validate_template_hours(db, employee_id, payload)

    template = EmployeeScheduleTemplate(employee_id=employee_id, **payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@app.patch(
    "/schedule-templates/{template_id}",
    response_model=EmployeeScheduleTemplateOut,
    dependencies=[Depends(require_admin)],
)
def update_schedule_template(
    template_id: int,
    payload: EmployeeScheduleTemplateUpdate,
    db: Session = Depends(get_db),
) -> EmployeeScheduleTemplate:
    template = db.get(EmployeeScheduleTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Schedule template not found")

    if templates_overlap(
        db, template.employee_id, payload.start_date, payload.end_date, exclude_id=template.id
    ):
        raise HTTPException(
            status_code=422,
            detail="Template date range overlaps an existing template for this employee",
        )
    if hours_exceed_cap(payload.work_start, payload.work_end, payload.max_hours_per_day):
        raise HTTPException(
            status_code=422,
            detail="Template hours exceed its own max hours per day",
        )

    for field, value in payload.model_dump().items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template


@app.delete("/schedule-templates/{template_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_schedule_template(template_id: int, db: Session = Depends(get_db)) -> None:
    template = db.get(EmployeeScheduleTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Schedule template not found")

    template.delete_flag = True
    db.commit()


def _validate_override_hours(
    db: Session,
    employee_id: int,
    target_date: date,
    day_type: DayType,
    work_start: time | None,
    work_end: time | None,
    max_hours_per_day: float | None,
) -> None:
    if day_type != DayType.WORKING:
        return
    if work_start is None or work_end is None:
        return
    template = covering_template(db, employee_id, target_date)
    cap = effective_max_hours_per_day(max_hours_per_day, template)
    if cap is not None and hours_exceed_cap(work_start, work_end, cap):
        raise HTTPException(
            status_code=422,
            detail="Override hours exceed the effective max hours per day",
        )


@app.get(
    "/employees/{employee_id}/schedule-overrides",
    response_model=list[EmployeeScheduleDayOverrideOut],
    dependencies=[Depends(require_admin)],
)
def list_schedule_overrides(
    employee_id: int, db: Session = Depends(get_db)
) -> list[EmployeeScheduleDayOverride]:
    return (
        db.query(EmployeeScheduleDayOverride)
        .filter(
            EmployeeScheduleDayOverride.employee_id == employee_id,
            EmployeeScheduleDayOverride.delete_flag.is_(False),
        )
        .order_by(EmployeeScheduleDayOverride.date)
        .all()
    )


@app.post(
    "/employees/{employee_id}/schedule-overrides",
    response_model=EmployeeScheduleDayOverrideOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_schedule_override(
    employee_id: int,
    payload: EmployeeScheduleDayOverrideCreate,
    db: Session = Depends(get_db),
) -> EmployeeScheduleDayOverride:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    if override_exists_for_date(db, employee_id, payload.date):
        raise HTTPException(
            status_code=422,
            detail="An override already exists for this employee and date",
        )
    _validate_override_hours(
        db,
        employee_id,
        payload.date,
        payload.day_type,
        payload.work_start,
        payload.work_end,
        payload.max_hours_per_day,
    )

    override = EmployeeScheduleDayOverride(employee_id=employee_id, **payload.model_dump())
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


@app.patch(
    "/schedule-overrides/{override_id}",
    response_model=EmployeeScheduleDayOverrideOut,
    dependencies=[Depends(require_admin)],
)
def update_schedule_override(
    override_id: int,
    payload: EmployeeScheduleDayOverrideUpdate,
    db: Session = Depends(get_db),
) -> EmployeeScheduleDayOverride:
    override = db.get(EmployeeScheduleDayOverride, override_id)
    if override is None:
        raise HTTPException(status_code=404, detail="Schedule override not found")

    _validate_override_hours(
        db,
        override.employee_id,
        override.date,
        payload.day_type,
        payload.work_start,
        payload.work_end,
        payload.max_hours_per_day,
    )

    for field, value in payload.model_dump().items():
        setattr(override, field, value)
    db.commit()
    db.refresh(override)
    return override


@app.delete("/schedule-overrides/{override_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_schedule_override(override_id: int, db: Session = Depends(get_db)) -> None:
    override = db.get(EmployeeScheduleDayOverride, override_id)
    if override is None:
        raise HTTPException(status_code=404, detail="Schedule override not found")

    override.delete_flag = True
    db.commit()


@app.post(
    "/employees/{employee_id}/schedule-overrides/bulk",
    response_model=list[EmployeeScheduleDayOverrideOut],
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_schedule_overrides_bulk(
    employee_id: int,
    payload: EmployeeScheduleDayOverrideBulkCreate,
    db: Session = Depends(get_db),
) -> list[EmployeeScheduleDayOverride]:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="end_date must not be before start_date")

    dates = [
        payload.start_date + timedelta(days=offset)
        for offset in range((payload.end_date - payload.start_date).days + 1)
    ]
    conflicting = [d for d in dates if override_exists_for_date(db, employee_id, d)]
    if conflicting:
        raise HTTPException(
            status_code=422,
            detail=f"An override already exists for this employee on: {conflicting[0].isoformat()}",
        )

    overrides = [
        EmployeeScheduleDayOverride(employee_id=employee_id, date=d, day_type=payload.day_type)
        for d in dates
    ]
    db.add_all(overrides)
    db.commit()
    for override in overrides:
        db.refresh(override)
    return overrides


@app.get("/regions", response_model=list[RegionOut], dependencies=[Depends(require_admin)])
def list_regions(db: Session = Depends(get_db)) -> list[Region]:
    return (
        db.query(Region)
        .filter(Region.delete_flag.is_(False))
        .order_by(Region.id)
        .all()
    )


@app.post("/regions", response_model=RegionOut, status_code=201, dependencies=[Depends(require_admin)])
def create_region(payload: RegionCreate, db: Session = Depends(get_db)) -> Region:
    region = Region(
        name=payload.name,
        geo_shape=[point.model_dump() for point in payload.geo_shape]
        if payload.geo_shape is not None
        else None,
    )
    db.add(region)
    db.commit()
    db.refresh(region)
    return region


@app.patch("/regions/{region_id}", response_model=RegionOut, dependencies=[Depends(require_admin)])
def update_region(
    region_id: int, payload: RegionUpdate, db: Session = Depends(get_db)
) -> Region:
    region = db.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    region.name = payload.name
    region.geo_shape = (
        [point.model_dump() for point in payload.geo_shape]
        if payload.geo_shape is not None
        else None
    )
    db.commit()
    db.refresh(region)
    return region


@app.delete("/regions/{region_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_region(region_id: int, db: Session = Depends(get_db)) -> None:
    region = db.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    region.delete_flag = True
    db.commit()


@app.get("/skills", response_model=list[SkillOut], dependencies=[Depends(require_admin)])
def list_skills(db: Session = Depends(get_db)) -> list[Skill]:
    return db.query(Skill).filter(Skill.delete_flag.is_(False)).order_by(Skill.id).all()


@app.post("/skills", response_model=SkillOut, status_code=201, dependencies=[Depends(require_admin)])
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)) -> Skill:
    skill = Skill(name=payload.name)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@app.patch("/skills/{skill_id}", response_model=SkillOut, dependencies=[Depends(require_admin)])
def update_skill(skill_id: int, payload: SkillUpdate, db: Session = Depends(get_db)) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill.name = payload.name
    db.commit()
    db.refresh(skill)
    return skill


@app.delete("/skills/{skill_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_skill(skill_id: int, db: Session = Depends(get_db)) -> None:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill.delete_flag = True
    db.commit()


@app.get("/service-order-types", response_model=list[ServiceOrderTypeOut], dependencies=[Depends(require_admin)])
def list_service_order_types(db: Session = Depends(get_db)) -> list[ServiceOrderType]:
    return (
        db.query(ServiceOrderType)
        .filter(ServiceOrderType.delete_flag.is_(False))
        .order_by(ServiceOrderType.id)
        .all()
    )


@app.post("/service-order-types", response_model=ServiceOrderTypeOut, status_code=201, dependencies=[Depends(require_admin)])
def create_service_order_type(
    payload: ServiceOrderTypeCreate, db: Session = Depends(get_db)
) -> ServiceOrderType:
    service_order_type = ServiceOrderType(name=payload.name)
    db.add(service_order_type)
    db.commit()
    db.refresh(service_order_type)
    return service_order_type


@app.patch("/service-order-types/{service_order_type_id}", response_model=ServiceOrderTypeOut, dependencies=[Depends(require_admin)])
def update_service_order_type(
    service_order_type_id: int,
    payload: ServiceOrderTypeUpdate,
    db: Session = Depends(get_db),
) -> ServiceOrderType:
    service_order_type = db.get(ServiceOrderType, service_order_type_id)
    if service_order_type is None:
        raise HTTPException(status_code=404, detail="Service order type not found")

    service_order_type.name = payload.name
    db.commit()
    db.refresh(service_order_type)
    return service_order_type


@app.delete("/service-order-types/{service_order_type_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_service_order_type(
    service_order_type_id: int, db: Session = Depends(get_db)
) -> None:
    service_order_type = db.get(ServiceOrderType, service_order_type_id)
    if service_order_type is None:
        raise HTTPException(status_code=404, detail="Service order type not found")

    service_order_type.delete_flag = True
    db.commit()


@app.post("/customer-locations/assign-regions", response_model=list[CustomerLocationOut], dependencies=[Depends(require_admin)])
def assign_customer_location_regions(db: Session = Depends(get_db)) -> list[CustomerLocation]:
    assign_regions_by_geofence(db)
    db.commit()
    return (
        db.query(CustomerLocation)
        .filter(CustomerLocation.delete_flag.is_(False), CustomerLocation.archived.is_(False))
        .options(
            joinedload(CustomerLocation.customer),
            joinedload(CustomerLocation.region),
        )
        .order_by(CustomerLocation.id)
        .all()
    )


@app.post("/regions/{region_id}/driving-times", response_model=DrivingTimeComputeSummary, dependencies=[Depends(require_admin)])
def compute_driving_times(region_id: int, db: Session = Depends(get_db)) -> dict:
    region = db.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    return compute_region_driving_times(db, region)


@app.get("/products", response_model=list[ProductOut])
def list_products(
    db: Session = Depends(get_db), user: User = Depends(require_session)
) -> list[Product]:
    query = db.query(Product).filter(
        Product.delete_flag.is_(False), Product.archived.is_(False)
    )
    if not user.is_admin:
        query = query.filter(Product.product_type == "PRD")
    return query.order_by(Product.number).all()


@app.post("/products/sync", response_model=list[ProductOut], dependencies=[Depends(require_admin)])
def sync_products_endpoint(db: Session = Depends(get_db)) -> list[Product]:
    try:
        sync_products(db)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Tripletex sync failed: {exc}"
        ) from exc
    return (
        db.query(Product)
        .filter(Product.delete_flag.is_(False), Product.archived.is_(False))
        .order_by(Product.number)
        .all()
    )


@app.post("/products", response_model=ProductOut, status_code=201, dependencies=[Depends(require_admin)])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    full_number = _prefixed_product_number(payload.product_type, payload.number)
    skills = _lookup_skills(db, payload.skill_ids)
    _validate_service_order_type_id(db, payload.service_order_type_id)

    product = Product(
        number=full_number,
        name=payload.name,
        product_type=payload.product_type,
        skills=skills,
        service_order_type_id=payload.service_order_type_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    failed_systems: list[str] = []
    client = _tripletex_client()
    try:
        data = client.create_product({"number": full_number, "name": payload.name})
        product.tripletex_id = data["id"]
        db.commit()
    except Exception:
        logger.warning("Tripletex push failed for product %s", product.id, exc_info=True)
        failed_systems.append("Tripletex")

    try:
        sync_product(db, product)
    except Exception:
        logger.warning("Resco sync failed for product %s", product.id, exc_info=True)
        failed_systems.append("Resco")

    product.sync_warning = _sync_warning(failed_systems)
    return product


@app.patch("/products/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)
) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    skills = _lookup_skills(db, payload.skill_ids)
    _validate_service_order_type_id(db, payload.service_order_type_id)

    full_number = _prefixed_product_number(payload.product_type, payload.number)
    product.number = full_number
    product.name = payload.name
    product.product_type = payload.product_type
    product.skills = skills
    product.service_order_type_id = payload.service_order_type_id
    db.commit()
    db.refresh(product)

    failed_systems: list[str] = []
    if product.tripletex_id is not None:
        client = _tripletex_client()
        try:
            client.update_product(product.tripletex_id, {"number": full_number, "name": payload.name})
        except Exception:
            logger.warning("Tripletex push failed for product %s", product.id, exc_info=True)
            failed_systems.append("Tripletex")

    try:
        sync_product(db, product)
    except Exception:
        logger.warning("Resco sync failed for product %s", product.id, exc_info=True)
        failed_systems.append("Resco")

    product.sync_warning = _sync_warning(failed_systems)
    return product


@app.delete("/products/{product_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product.archived = True
    db.commit()


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(
    db: Session = Depends(get_db), user: User = Depends(require_session)
) -> list[Customer]:
    query = db.query(Customer).filter(
        Customer.delete_flag.is_(False), Customer.archived.is_(False)
    )
    scope = customer_scope_ids(user)
    if scope is not None:
        query = query.filter(Customer.id.in_(scope))
    return query.order_by(Customer.id).all()


@app.post(
    "/customers/sync", response_model=list[CustomerOut], dependencies=[Depends(require_admin)]
)
def sync_customers_endpoint(db: Session = Depends(get_db)) -> list[Customer]:
    try:
        sync_customers(db)
        sync_customer_locations(db)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Tripletex sync failed: {exc}"
        ) from exc
    return (
        db.query(Customer)
        .filter(Customer.delete_flag.is_(False), Customer.archived.is_(False))
        .order_by(Customer.id)
        .all()
    )


@app.post("/customers/sync-resco", response_model=RescoSyncSummary, dependencies=[Depends(require_admin)])
def sync_customers_to_resco_endpoint(db: Session = Depends(get_db)) -> RescoSyncSummary:
    return sync_customers_to_resco(db)


@app.post("/customers", response_model=CustomerOut, status_code=201, dependencies=[Depends(require_admin)])
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)

    failed_systems: list[str] = []
    client = _tripletex_client()
    try:
        data = client.create_customer({"name": payload.name})
        customer.tripletex_id = data["id"]
        db.commit()
    except Exception:
        logger.warning("Tripletex push failed for customer %s", customer.id, exc_info=True)
        failed_systems.append("Tripletex")

    try:
        result = sync_customer(db, customer)
        if result.status == "failed":
            failed_systems.append("Resco")
    except Exception:
        logger.warning("Resco sync failed for customer %s", customer.id, exc_info=True)
        failed_systems.append("Resco")

    customer.sync_warning = _sync_warning(failed_systems)
    return customer


@app.patch("/customers/{customer_id}", response_model=CustomerOut, dependencies=[Depends(require_admin)])
def update_customer(
    customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.name = payload.name
    if "contact_name" in payload.model_fields_set:
        customer.contact_name = payload.contact_name
    if "phone_number_mobile" in payload.model_fields_set:
        customer.phone_number_mobile = payload.phone_number_mobile
    customer.email = payload.email
    customer.phone_number = payload.phone_number
    customer.organization_number = payload.organization_number
    db.commit()
    db.refresh(customer)

    failed_systems: list[str] = []
    if customer.tripletex_id is not None:
        client = _tripletex_client()
        try:
            client.update_customer(
                customer.tripletex_id,
                {
                    "name": payload.name,
                    "email": payload.email,
                    "phoneNumber": payload.phone_number,
                    "organizationNumber": payload.organization_number,
                },
            )
        except Exception:
            logger.warning("Tripletex push failed for customer %s", customer.id, exc_info=True)
            failed_systems.append("Tripletex")

    try:
        result = sync_customer(db, customer)
        if result.status == "failed":
            failed_systems.append("Resco")
    except Exception:
        logger.warning("Resco sync failed for customer %s", customer.id, exc_info=True)
        failed_systems.append("Resco")

    customer.sync_warning = _sync_warning(failed_systems)
    return customer


@app.delete("/customers/{customer_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> None:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.archived = True
    db.commit()


@app.get("/customer-locations", response_model=list[CustomerLocationOut])
def list_customer_locations(
    db: Session = Depends(get_db), user: User = Depends(require_session)
) -> list[CustomerLocation]:
    query = db.query(CustomerLocation).filter(
        CustomerLocation.delete_flag.is_(False), CustomerLocation.archived.is_(False)
    )
    scope = customer_scope_ids(user)
    if scope is not None:
        query = query.filter(CustomerLocation.customer_id.in_(scope))
    return (
        query.options(
            joinedload(CustomerLocation.customer),
            joinedload(CustomerLocation.region),
        )
        .order_by(CustomerLocation.id)
        .all()
    )


@app.post("/customer-locations/sync-resco", response_model=RescoSyncSummary, dependencies=[Depends(require_admin)])
def sync_customer_locations_to_resco_endpoint(db: Session = Depends(get_db)) -> RescoSyncSummary:
    return sync_customer_locations_to_resco(db)


@app.patch("/customer-locations/{location_id}/coordinates", response_model=CustomerLocationOut, dependencies=[Depends(require_admin)])
def update_customer_location_coordinates(
    location_id: int,
    payload: CustomerLocationCoordinatesUpdate,
    db: Session = Depends(get_db),
) -> CustomerLocation:
    location = db.get(CustomerLocation, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Customer location not found")

    location.latitude = payload.latitude
    location.longitude = payload.longitude
    location.coordinates_locked = payload.coordinates_locked
    db.commit()
    db.refresh(location)
    return location


@app.post("/customer-locations", response_model=CustomerLocationOut, status_code=201, dependencies=[Depends(require_admin)])
def create_customer_location(
    payload: CustomerLocationCreate, db: Session = Depends(get_db)
) -> CustomerLocation:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    location = CustomerLocation(
        customer_id=customer.id,
        address_line_1=payload.address_line_1,
        address_line_2=payload.address_line_2,
        postal_code=payload.postal_code,
        city=payload.city,
        address=_customer_location_display_address(
            payload.address_line_1, payload.postal_code, payload.city
        ),
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    resolved = geocode_address(location.address)
    if resolved is not None:
        location.latitude, location.longitude = resolved
        db.commit()
        db.refresh(location)

    failed_systems: list[str] = []
    if customer.tripletex_id is not None:
        client = _tripletex_client()
        try:
            data = client.create_delivery_address(
                customer.tripletex_id,
                {
                    "addressLine1": payload.address_line_1,
                    "addressLine2": payload.address_line_2,
                    "postalCode": payload.postal_code,
                    "city": payload.city,
                },
            )
            location.tripletex_id = data["id"]
            db.commit()
        except Exception:
            logger.warning(
                "Tripletex push failed for customer location %s", location.id, exc_info=True
            )
            failed_systems.append("Tripletex")
    else:
        failed_systems.append("Tripletex")

    try:
        result = sync_customer_location(db, location)
        if result.status == "failed":
            failed_systems.append("Resco")
    except Exception:
        logger.warning(
            "Resco sync failed for customer location %s", location.id, exc_info=True
        )
        failed_systems.append("Resco")

    location.sync_warning = _sync_warning(failed_systems)
    return location


@app.patch("/customer-locations/{location_id}", response_model=CustomerLocationOut, dependencies=[Depends(require_admin)])
def update_customer_location(
    location_id: int, payload: CustomerLocationUpdate, db: Session = Depends(get_db)
) -> CustomerLocation:
    location = db.get(CustomerLocation, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Customer location not found")

    location.address_line_1 = payload.address_line_1
    location.address_line_2 = payload.address_line_2
    location.postal_code = payload.postal_code
    location.city = payload.city
    location.address = _customer_location_display_address(
        payload.address_line_1, payload.postal_code, payload.city
    )
    if not location.coordinates_locked:
        resolved = geocode_address(location.address)
        if resolved is not None:
            location.latitude, location.longitude = resolved
    db.commit()
    db.refresh(location)

    failed_systems: list[str] = []
    if location.tripletex_id is not None:
        client = _tripletex_client()
        try:
            client.update_delivery_address(
                location.tripletex_id,
                {
                    "addressLine1": payload.address_line_1,
                    "addressLine2": payload.address_line_2,
                    "postalCode": payload.postal_code,
                    "city": payload.city,
                },
            )
        except Exception:
            logger.warning(
                "Tripletex push failed for customer location %s", location.id, exc_info=True
            )
            failed_systems.append("Tripletex")

    try:
        result = sync_customer_location(db, location)
        if result.status == "failed":
            failed_systems.append("Resco")
    except Exception:
        logger.warning(
            "Resco sync failed for customer location %s", location.id, exc_info=True
        )
        failed_systems.append("Resco")

    location.sync_warning = _sync_warning(failed_systems)
    return location


@app.delete("/customer-locations/{location_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_customer_location(location_id: int, db: Session = Depends(get_db)) -> None:
    location = db.get(CustomerLocation, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Customer location not found")

    location.archived = True
    db.commit()


def _contract_out(contract: Contract) -> ContractOut:
    return ContractOut(
        id=contract.id,
        customer=CustomerOut.model_validate(contract.customer),
        lines=[
            ContractLineOut.model_validate(line)
            for line in contract.lines
            if not line.delete_flag
        ],
    )


@app.get("/contracts", response_model=list[ContractOut])
def list_contracts(
    db: Session = Depends(get_db), user: User = Depends(require_session)
) -> list[ContractOut]:
    query = db.query(Contract).filter(Contract.delete_flag.is_(False))
    scope = customer_scope_ids(user)
    if scope is not None:
        query = query.filter(Contract.customer_id.in_(scope))
    contracts = (
        query.options(
            joinedload(Contract.customer),
            joinedload(Contract.lines)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(Contract.lines)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
            joinedload(Contract.lines)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.skills),
            joinedload(Contract.lines)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.service_order_type),
        )
        .order_by(Contract.id)
        .all()
    )
    return [_contract_out(contract) for contract in contracts]


@app.post("/contracts", response_model=ContractOut, status_code=201, dependencies=[Depends(require_admin)])
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)) -> ContractOut:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    contract = Contract(customer_id=customer.id)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return _contract_out(contract)


@app.patch("/contracts/{contract_id}", response_model=ContractOut, dependencies=[Depends(require_admin)])
def update_contract(
    contract_id: int, payload: ContractUpdate, db: Session = Depends(get_db)
) -> ContractOut:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    contract.customer_id = customer.id
    db.commit()
    db.refresh(contract)
    return _contract_out(contract)


def _delete_service_visits_for_line(db: Session, line_id: int) -> None:
    visit_ids = [
        visit_id
        for (visit_id,) in db.query(ServiceVisit.id).filter(
            ServiceVisit.contract_line_id == line_id
        )
    ]
    if visit_ids:
        db.query(Assignment).filter(Assignment.service_visit_id.in_(visit_ids)).delete(
            synchronize_session=False
        )
        db.query(ServiceVisit).filter(ServiceVisit.id.in_(visit_ids)).delete(
            synchronize_session=False
        )


def _is_started(assignment: Assignment) -> bool:
    """An assignment counts as started once its planned start time has
    passed — the same definition the assignments capability uses to lock
    an assignment regardless of its stored pin flag."""
    return assignment.planned_start <= datetime.now()


def _regenerate_future_visits(db: Session, line: ContractLine) -> None:
    """Remove every one of this contract line's not-yet-started service
    visits (unassigned, or assigned but not started, pinned or not) and
    regenerate its future visits from the line's current terms, anchored
    at its last-started visit if one exists, or its start_date otherwise.
    Visits with a started assignment are never touched."""
    visits = (
        db.query(ServiceVisit)
        .options(joinedload(ServiceVisit.assignment))
        .filter(ServiceVisit.contract_line_id == line.id)
        .all()
    )
    started_dates = [
        visit.requested_date
        for visit in visits
        if visit.assignment is not None and _is_started(visit.assignment)
    ]
    not_started_ids = [
        visit.id
        for visit in visits
        if visit.assignment is None or not _is_started(visit.assignment)
    ]

    if not_started_ids:
        db.query(Assignment).filter(
            Assignment.service_visit_id.in_(not_started_ids)
        ).delete(synchronize_session=False)
        db.query(ServiceVisit).filter(ServiceVisit.id.in_(not_started_ids)).delete(
            synchronize_session=False
        )

    today = date.today()
    horizon = line.end_date or (today + timedelta(days=OPEN_ENDED_HORIZON_DAYS))
    anchor = max(started_dates) if started_dates else None

    if anchor is not None:
        occurrence_dates = extend_occurrence_dates(
            line.start_date, line.interval_unit, line.interval_count, anchor, horizon
        )
    elif horizon < today:
        occurrence_dates = []
    else:
        occurrence_dates = generate_occurrence_dates(
            line.start_date, line.interval_unit, line.interval_count, horizon
        )
        if line.start_date < today:
            occurrence_dates = [today] + [d for d in occurrence_dates if d > today]

    for occurrence_date in occurrence_dates:
        db.add(ServiceVisit(contract_line_id=line.id, requested_date=occurrence_date))


@app.delete("/contracts/{contract_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_contract(contract_id: int, db: Session = Depends(get_db)) -> None:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract.delete_flag = True
    for line in contract.lines:
        line.delete_flag = True
        _delete_service_visits_for_line(db, line.id)
    db.commit()


@app.post("/contracts/{contract_id}/lines", response_model=ContractLineOut, status_code=201, dependencies=[Depends(require_admin)])
def create_contract_line(
    contract_id: int, payload: ContractLineCreate, db: Session = Depends(get_db)
) -> ContractLine:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    customer_location = db.get(CustomerLocation, payload.customer_location_id)
    if customer_location is None:
        raise HTTPException(status_code=404, detail="Customer location not found")
    if customer_location.customer_id != contract.customer_id:
        raise HTTPException(
            status_code=422,
            detail="Customer location does not belong to the contract's customer",
        )

    required_products = db.query(Product).filter(Product.id.in_(payload.required_product_ids)).all()
    if len(required_products) != len(set(payload.required_product_ids)):
        raise HTTPException(status_code=404, detail="One or more products not found")

    line = ContractLine(
        contract_id=contract.id,
        customer_location_id=customer_location.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        interval_unit=payload.interval_unit,
        interval_count=payload.interval_count,
        duration_minutes=payload.duration_minutes,
        priority=payload.priority,
        required_products=required_products,
    )
    db.add(line)
    db.flush()

    occurrence_dates = generate_occurrence_dates(
        line.start_date, line.interval_unit, line.interval_count, line.end_date
    )
    for occurrence_date in occurrence_dates:
        db.add(ServiceVisit(contract_line_id=line.id, requested_date=occurrence_date))

    db.commit()
    db.refresh(line)
    return line


@app.post("/contract-lines/extend-visits", response_model=ContractLineExtendSummary, dependencies=[Depends(require_admin)])
def extend_contract_line_visits(db: Session = Depends(get_db)) -> dict:
    """Top up every open-ended contract line's generated visits back out to
    OPEN_ENDED_HORIZON_DAYS ahead of today, generating only the occurrences
    past each line's current furthest generated one."""
    new_horizon = date.today() + timedelta(days=OPEN_ENDED_HORIZON_DAYS)

    lines = (
        db.query(ContractLine)
        .filter(ContractLine.delete_flag.is_(False), ContractLine.end_date.is_(None))
        .all()
    )

    lines_extended = 0
    visits_created = 0
    for line in lines:
        furthest_existing = (
            db.query(func.max(ServiceVisit.requested_date))
            .filter(ServiceVisit.contract_line_id == line.id)
            .scalar()
        ) or line.start_date

        occurrence_dates = extend_occurrence_dates(
            line.start_date, line.interval_unit, line.interval_count, furthest_existing, new_horizon
        )
        if not occurrence_dates:
            continue

        for occurrence_date in occurrence_dates:
            db.add(ServiceVisit(contract_line_id=line.id, requested_date=occurrence_date))
        lines_extended += 1
        visits_created += len(occurrence_dates)

    db.commit()
    return {"lines_extended": lines_extended, "visits_created": visits_created}


def _check_contract_line_customer_access(line: ContractLine, user: User) -> None:
    scope = customer_scope_ids(user)
    if scope is not None and line.customer_location.customer_id not in scope:
        raise HTTPException(status_code=403, detail="Customer access required")


@app.get("/contract-lines/{line_id}/free-slots", response_model=list[FreeSlotOut])
def get_contract_line_free_slots(
    line_id: int, db: Session = Depends(get_db), user: User = Depends(require_session)
) -> list[FreeSlotOut]:
    line = db.get(ContractLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Contract line not found")
    _check_contract_line_customer_access(line, user)

    return [
        FreeSlotOut(
            employee_id=slot.employee_id,
            employee_name=slot.employee_name,
            start=slot.start,
            end=slot.end,
        )
        for slot in find_free_slots(db, line)
    ]


@app.post(
    "/contract-lines/{line_id}/ad-hoc-visits", response_model=AssignmentOut, status_code=201
)
def book_ad_hoc_visit(
    line_id: int,
    payload: AdHocVisitCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_session),
) -> Assignment:
    line = db.get(ContractLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Contract line not found")
    _check_contract_line_customer_access(line, user)

    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    visit = ServiceVisit(contract_line_id=line.id, requested_date=payload.start.date())
    db.add(visit)
    db.flush()

    assignment = _assign_visit(db, visit, employee, payload.start)
    db.commit()
    db.refresh(assignment)
    return assignment


@app.patch("/contract-lines/{line_id}", response_model=ContractLineOut, dependencies=[Depends(require_admin)])
def update_contract_line(
    line_id: int, payload: ContractLineUpdate, db: Session = Depends(get_db)
) -> ContractLine:
    line = db.get(ContractLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Contract line not found")

    customer_location = db.get(CustomerLocation, payload.customer_location_id)
    if customer_location is None:
        raise HTTPException(status_code=404, detail="Customer location not found")
    if customer_location.customer_id != line.contract.customer_id:
        raise HTTPException(
            status_code=422,
            detail="Customer location does not belong to the contract's customer",
        )

    required_products = db.query(Product).filter(Product.id.in_(payload.required_product_ids)).all()
    if len(required_products) != len(set(payload.required_product_ids)):
        raise HTTPException(status_code=404, detail="One or more products not found")

    line.customer_location_id = customer_location.id
    line.start_date = payload.start_date
    line.end_date = payload.end_date
    line.interval_unit = payload.interval_unit
    line.interval_count = payload.interval_count
    line.duration_minutes = payload.duration_minutes
    line.priority = payload.priority
    line.required_products = required_products
    db.flush()
    _regenerate_future_visits(db, line)
    db.commit()
    db.refresh(line)
    return line


@app.delete("/contract-lines/{line_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_contract_line(line_id: int, db: Session = Depends(get_db)) -> None:
    line = db.get(ContractLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Contract line not found")

    line.delete_flag = True
    _delete_service_visits_for_line(db, line.id)
    db.commit()


@app.get("/service-visits", response_model=list[ServiceVisitOut])
def list_service_visits(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_session),
) -> list[ServiceVisit]:
    query = db.query(ServiceVisit).options(
        joinedload(ServiceVisit.contract_line)
        .joinedload(ContractLine.required_products)
        .joinedload(Product.skills),
        joinedload(ServiceVisit.contract_line)
        .joinedload(ContractLine.customer_location)
        .joinedload(CustomerLocation.customer),
        joinedload(ServiceVisit.contract_line)
        .joinedload(ContractLine.customer_location)
        .joinedload(CustomerLocation.region),
    )
    scope = customer_scope_ids(user)
    if scope is not None:
        query = query.join(ServiceVisit.contract_line).join(
            ContractLine.customer_location
        ).filter(CustomerLocation.customer_id.in_(scope))
    if start_date is not None:
        query = query.filter(ServiceVisit.requested_date >= start_date)
    if end_date is not None:
        query = query.filter(ServiceVisit.requested_date <= end_date)
    return query.order_by(ServiceVisit.id).all()


@app.get("/assignments", response_model=list[AssignmentOut], dependencies=[Depends(require_admin)])
def list_assignments(db: Session = Depends(get_db)) -> list[Assignment]:
    return (
        db.query(Assignment)
        .options(
            joinedload(Assignment.employee).joinedload(Employee.regions),
            joinedload(Assignment.employee).joinedload(Employee.skills),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.skills),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
        )
        .order_by(Assignment.service_visit_id)
        .all()
    )


@app.get("/day-planning/routes", response_model=DayPlanningRoutesOut, dependencies=[Depends(require_admin)])
def get_day_planning_routes(date: date, db: Session = Depends(get_db)) -> DayPlanningRoutesOut:
    day_start = datetime.combine(date, time())
    day_end = day_start + timedelta(days=1)

    assignments = (
        db.query(Assignment)
        .join(Assignment.employee)
        .filter(
            Assignment.planned_start >= day_start,
            Assignment.planned_start < day_end,
            Employee.delete_flag.is_(False),
        )
        .options(
            joinedload(Assignment.employee),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
        )
        .order_by(Assignment.employee_id, Assignment.planned_start)
        .all()
    )

    assignments_by_employee: dict[int, list[Assignment]] = {}
    for assignment in assignments:
        location = assignment.service_visit.contract_line.customer_location
        if location.latitude is None or location.longitude is None:
            continue
        assignments_by_employee.setdefault(assignment.employee_id, []).append(assignment)

    employee_routes: list[DayPlanningEmployeeRouteOut] = []
    for employee_assignments in assignments_by_employee.values():
        employee = employee_assignments[0].employee
        stops = [LocationEndpoint(LocationKind.EMPLOYEE, employee.id, employee.latitude, employee.longitude)]
        for assignment in employee_assignments:
            location = assignment.service_visit.contract_line.customer_location
            stops.append(
                LocationEndpoint(
                    LocationKind.CUSTOMER_LOCATION, location.id, location.latitude, location.longitude
                )
            )

        route_points = compute_employee_day_route(stops)
        if route_points is None:
            continue

        stop_outs = [
            DayPlanningStopOut(
                kind=LocationKind.EMPLOYEE,
                latitude=employee.latitude,
                longitude=employee.longitude,
            )
        ]
        for assignment in employee_assignments:
            location = assignment.service_visit.contract_line.customer_location
            stop_outs.append(
                DayPlanningStopOut(
                    kind=LocationKind.CUSTOMER_LOCATION,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    service_visit_id=assignment.service_visit_id,
                    customer_name=location.customer.name,
                    planned_start=assignment.planned_start,
                    planned_end=assignment.planned_end,
                )
            )

        employee_routes.append(
            DayPlanningEmployeeRouteOut(
                employee_id=employee.id,
                employee_name=employee.name,
                stops=stop_outs,
                route=[GeoPoint(lat=p.latitude, lng=p.longitude) for p in route_points],
            )
        )

    return DayPlanningRoutesOut(employees=employee_routes)


@app.post("/demo/refresh-schedule", response_model=DemoScheduleRefreshSummary, dependencies=[Depends(require_admin)])
def post_refresh_demo_schedule(db: Session = Depends(get_db)) -> dict:
    return refresh_demo_schedule(db)


def _assign_visit(
    db: Session, visit: ServiceVisit, employee: Employee, planned_start: datetime
) -> Assignment:
    """Create an assignment for a visit and mark it assigned. Callers are
    responsible for whatever existence/status checks their own flow needs."""
    planned_end = planned_start + timedelta(minutes=visit.contract_line.duration_minutes)
    assignment = Assignment(
        service_visit_id=visit.id,
        employee_id=employee.id,
        planned_start=planned_start,
        planned_end=planned_end,
    )
    visit.unassigned_reason = None
    visit.status = VisitStatus.ASSIGNED
    db.add(assignment)
    return assignment


@app.post("/assignments", response_model=AssignmentOut, status_code=201, dependencies=[Depends(require_admin)])
def create_assignment(
    payload: AssignmentCreate, db: Session = Depends(get_db)
) -> Assignment:
    visit = db.get(ServiceVisit, payload.service_visit_id)
    if visit is None:
        raise HTTPException(status_code=404, detail="Service visit not found")

    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    if visit.status == VisitStatus.ASSIGNED:
        raise HTTPException(
            status_code=409, detail="Service visit is already assigned"
        )

    assignment = _assign_visit(db, visit, employee, payload.planned_start)
    db.commit()
    db.refresh(assignment)

    try:
        resco_sync = sync_assignment(db, assignment)
    except Exception:
        logger.warning("Resco sync failed for assignment %s", assignment.service_visit_id, exc_info=True)
        resco_sync = AssignmentRescoSyncResult(status="failed", detail="Resco sync failed")
    assignment.resco_sync = resco_sync

    return assignment


@app.delete("/assignments/{service_visit_id}", status_code=204, dependencies=[Depends(require_admin)])
def unassign_visit(service_visit_id: int, db: Session = Depends(get_db)) -> None:
    assignment = db.get(Assignment, service_visit_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    visit = assignment.service_visit
    db.delete(assignment)
    visit.status = VisitStatus.UNASSIGNED
    db.commit()


@app.patch("/assignments/{service_visit_id}", response_model=AssignmentOut, dependencies=[Depends(require_admin)])
def update_assignment_pin(
    service_visit_id: int, payload: AssignmentPinUpdate, db: Session = Depends(get_db)
) -> Assignment:
    assignment = db.get(Assignment, service_visit_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.pinned = payload.pinned
    db.commit()
    db.refresh(assignment)
    return assignment


@app.post("/optimize/propose", response_model=OptimizationProposal, dependencies=[Depends(require_admin)])
def propose_optimization(
    options: OptimizeRunOptions | None = None, db: Session = Depends(get_db)
) -> OptimizationProposal:
    options = options or OptimizeRunOptions()

    # `parallel` always attempts a split; `single` also splits automatically
    # once the run's ready-visit count crosses parallel_split_visit_threshold
    # - see solver_client.resolve_run_payloads and design.md's "Mandatory
    # region-splitting above a problem-size threshold".
    payload, group_payloads, excluded_visit_ids = resolve_run_payloads(
        db,
        days_ahead=options.days_ahead,
        time_limit_seconds=options.time_limit_seconds,
        plan_from_time=options.plan_from_time,
        force_split=options.execution_mode == "parallel",
    )

    if group_payloads is not None:
        try:
            result = request_parallel_proposals(group_payloads)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail=f"Solver request failed: {exc}"
            ) from exc
    else:
        assert payload is not None
        try:
            result = request_proposal(payload)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail=f"Solver request failed: {exc}"
            ) from exc

    visits_by_id = {
        v.id: v
        for v in db.query(ServiceVisit)
        .options(
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.skills),
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
        )
        .all()
    }
    employees_by_id = {
        e.id: e
        for e in db.query(Employee)
        .options(joinedload(Employee.regions), joinedload(Employee.skills))
        .all()
    }

    scheduled = []
    for item in result["scheduled"]:
        visit = visits_by_id[item["visit_id"]]
        employee = employees_by_id[item["employee_id"]]
        # The date the solver actually chose for this visit - may differ
        # from its nominal requested_date; see add-multi-day-scheduling-window.
        day_start = datetime.combine(date.fromisoformat(item["date"]), time())
        scheduled.append(
            ProposedAssignmentOut(
                service_visit_id=visit.id,
                employee_id=employee.id,
                planned_start=day_start + timedelta(minutes=item["start_minutes"]),
                planned_end=day_start + timedelta(minutes=item["end_minutes"]),
                employee=employee,
                service_visit=visit,
            )
        )

    return OptimizationProposal(
        scheduled=scheduled,
        unscheduled_visit_ids=result["unscheduled_visit_ids"] + excluded_visit_ids,
    )


@app.post("/optimize/apply", response_model=OptimizationApplyResult, dependencies=[Depends(require_admin)])
def apply_optimization(
    payload: OptimizationApplyRequest, db: Session = Depends(get_db)
) -> OptimizationApplyResult:
    results: list[Assignment] = []
    skipped: list[int] = []
    for item in payload.scheduled:
        visit = db.get(ServiceVisit, item.service_visit_id)
        if visit is None:
            raise HTTPException(
                status_code=404,
                detail=f"Service visit {item.service_visit_id} not found",
            )

        assignment = db.get(Assignment, item.service_visit_id)
        if assignment is None:
            results.append(create_assignment(item, db))
            continue

        if assignment.pinned:
            skipped.append(item.service_visit_id)
            continue

        employee = db.get(Employee, item.employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")

        visit.unassigned_reason = None
        assignment.employee_id = employee.id
        assignment.planned_start = item.planned_start
        assignment.planned_end = item.planned_start + timedelta(
            minutes=visit.contract_line.duration_minutes
        )
        db.commit()
        db.refresh(assignment)

        try:
            resco_sync = sync_assignment(db, assignment)
        except Exception:
            logger.warning("Resco sync failed for assignment %s", assignment.service_visit_id, exc_info=True)
            resco_sync = AssignmentRescoSyncResult(status="failed", detail="Resco sync failed")
        assignment.resco_sync = resco_sync

        results.append(assignment)

    return OptimizationApplyResult(created=results, skipped_visit_ids=skipped)


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_admin=user.is_admin,
        customer_ids=[customer.id for customer in user.customers],
    )


def _current_user_out(user: User) -> CurrentUserOut:
    return CurrentUserOut(
        id=user.id,
        email=user.email,
        is_admin=user.is_admin,
        customer_ids=[customer.id for customer in user.customers],
    )


@app.post("/auth/signup", response_model=UserOut, status_code=201)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = (
        db.query(User)
        .filter(User.email == payload.email, User.delete_flag.is_(False))
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already in use")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.post("/auth/login", response_model=CurrentUserOut)
def login(payload: UserLoginRequest, response: Response, db: Session = Depends(get_db)) -> CurrentUserOut:
    user = (
        db.query(User)
        .filter(User.email == payload.email, User.delete_flag.is_(False))
        .first()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_session_token(user)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
    )
    return _current_user_out(user)


@app.post("/auth/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME)


@app.get("/auth/me", response_model=CurrentUserOut | None)
def get_me(user: User | None = Depends(get_current_user)) -> CurrentUserOut | None:
    if user is None:
        return None
    return _current_user_out(user)


@app.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    users = db.query(User).filter(User.delete_flag.is_(False)).order_by(User.id).all()
    return [_user_out(user) for user in users]


@app.patch(
    "/users/{user_id}/customers",
    response_model=UserOut,
    dependencies=[Depends(require_admin)],
)
def update_user_customers(
    user_id: int, payload: UserCustomersUpdate, db: Session = Depends(get_db)
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    customers = db.query(Customer).filter(Customer.id.in_(payload.customer_ids)).all()
    if len(customers) != len(set(payload.customer_ids)):
        raise HTTPException(status_code=404, detail="One or more customers not found")

    user.customers = customers
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.patch(
    "/users/{user_id}/admin",
    response_model=UserOut,
    dependencies=[Depends(require_admin)],
)
def update_user_admin(
    user_id: int, payload: UserAdminUpdate, db: Session = Depends(get_db)
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = payload.is_admin
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.post(
    "/users/{user_id}/reset-password",
    response_model=UserOut,
    dependencies=[Depends(require_admin)],
)
def reset_user_password(
    user_id: int, payload: UserPasswordReset, db: Session = Depends(get_db)
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.post("/service-requests", response_model=ServiceRequestOut, status_code=201)
def create_service_request(
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_session),
) -> ServiceRequest:
    scope = customer_scope_ids(user)
    if scope is not None and payload.customer_id not in scope:
        raise HTTPException(status_code=403, detail="Customer access required")

    location = db.get(CustomerLocation, payload.customer_location_id)
    if location is None or location.customer_id != payload.customer_id:
        raise HTTPException(
            status_code=422, detail="Customer location does not belong to the given customer"
        )

    product = db.get(Product, payload.product_id)
    if product is None or product.delete_flag or product.product_type != "PRD":
        raise HTTPException(
            status_code=422, detail="Product must be a non-deleted PRD-type product"
        )

    request = ServiceRequest(
        customer_id=payload.customer_id,
        customer_location_id=payload.customer_location_id,
        product_id=payload.product_id,
        note=payload.note,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@app.get(
    "/service-requests",
    response_model=list[ServiceRequestOut],
    dependencies=[Depends(require_admin)],
)
def list_service_requests(
    status: ServiceRequestStatus = ServiceRequestStatus.PENDING, db: Session = Depends(get_db)
) -> list[ServiceRequest]:
    return (
        db.query(ServiceRequest)
        .filter(ServiceRequest.status == status)
        .options(
            joinedload(ServiceRequest.customer),
            joinedload(ServiceRequest.customer_location).joinedload(CustomerLocation.customer),
            joinedload(ServiceRequest.customer_location).joinedload(CustomerLocation.region),
            joinedload(ServiceRequest.product).joinedload(Product.skills),
            joinedload(ServiceRequest.product).joinedload(Product.service_order_type),
        )
        .order_by(ServiceRequest.created_at)
        .all()
    )


@app.patch(
    "/service-requests/{request_id}",
    response_model=ServiceRequestOut,
    dependencies=[Depends(require_admin)],
)
def acknowledge_service_request(request_id: int, db: Session = Depends(get_db)) -> ServiceRequest:
    request = db.get(ServiceRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Service request not found")

    request.status = ServiceRequestStatus.ACKNOWLEDGED
    db.commit()
    db.refresh(request)
    return request


@app.get(
    "/customers/{customer_id}/dashboard",
    response_model=CustomerDashboardOut,
)
def get_customer_dashboard(
    customer_id: int, db: Session = Depends(get_db), user: User = Depends(require_customer_access)
) -> CustomerDashboardOut:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    locations = (
        db.query(CustomerLocation)
        .filter(
            CustomerLocation.customer_id == customer_id,
            CustomerLocation.delete_flag.is_(False),
            CustomerLocation.archived.is_(False),
        )
        .options(joinedload(CustomerLocation.customer), joinedload(CustomerLocation.region))
        .order_by(CustomerLocation.id)
        .all()
    )

    contracts = (
        db.query(Contract)
        .filter(Contract.customer_id == customer_id, Contract.delete_flag.is_(False))
        .options(
            joinedload(Contract.customer),
            joinedload(Contract.lines)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(Contract.lines)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
            joinedload(Contract.lines)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.skills),
            joinedload(Contract.lines)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.service_order_type),
        )
        .order_by(Contract.id)
        .all()
    )

    upcoming_visits = (
        db.query(ServiceVisit)
        .join(ServiceVisit.contract_line)
        .join(ContractLine.customer_location)
        .filter(
            CustomerLocation.customer_id == customer_id,
            ServiceVisit.requested_date >= date.today(),
        )
        .options(
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.required_products)
            .joinedload(Product.skills),
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
        )
        .order_by(ServiceVisit.requested_date)
        .all()
    )

    return CustomerDashboardOut(
        customer=CustomerOut.model_validate(customer),
        customer_locations=[CustomerLocationOut.model_validate(loc) for loc in locations],
        contracts=[_contract_out(contract) for contract in contracts],
        upcoming_visits=[ServiceVisitOut.model_validate(visit) for visit in upcoming_visits],
    )


@app.post("/assignments/sync-resco-status", response_model=RescoStatusSyncSummary,
          dependencies=[Depends(require_admin)])
def sync_assignment_statuses_endpoint(db: Session = Depends(get_db)) -> RescoStatusSyncSummary:
    return sync_assignment_statuses_from_resco(db)
