import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal, get_db
from app.employee_schedule import (
    covering_template,
    effective_max_hours_per_day,
    hours_exceed_cap,
    override_exists_for_date,
    templates_overlap,
)
from app.visit_generation import generate_occurrence_dates
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
    Region,
    ServiceVisit,
    Skill,
    VisitStatus,
)
from app.schemas import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentPinUpdate,
    ContractCreate,
    ContractLineCreate,
    ContractLineOut,
    ContractLineUpdate,
    ContractOut,
    ContractUpdate,
    CustomerLocationOut,
    CustomerOut,
    EmployeeCreate,
    EmployeeOut,
    EmployeeScheduleDayOverrideBulkCreate,
    EmployeeScheduleDayOverrideCreate,
    EmployeeScheduleDayOverrideOut,
    EmployeeScheduleDayOverrideUpdate,
    EmployeeScheduleTemplateCreate,
    EmployeeScheduleTemplateOut,
    EmployeeScheduleTemplateUpdate,
    EmployeeUpdate,
    OptimizationApplyRequest,
    OptimizationApplyResult,
    OptimizationProposal,
    ProposedAssignmentOut,
    RegionCreate,
    RegionOut,
    RegionUpdate,
    ServiceVisitOut,
    SkillCreate,
    SkillOut,
    SkillUpdate,
)
from app.solver_client import build_optimize_payload, effective_schedule_date, request_proposal
from app.tripletex import sync_customer_locations, sync_customers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        sync_customers(db)
        sync_customer_locations(db)
        logger.info("Tripletex customer/location sync succeeded at startup")
    except Exception:
        logger.warning("Tripletex customer/location sync failed at startup", exc_info=True)
    finally:
        db.close()
    yield


app = FastAPI(title="fms_ros", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _employee_out(employee: Employee) -> EmployeeOut:
    return EmployeeOut(
        id=employee.id,
        name=employee.name,
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


@app.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)) -> list[EmployeeOut]:
    employees = (
        _employee_query(db)
        .filter(Employee.delete_flag.is_(False))
        .order_by(Employee.id)
        .all()
    )
    return [_employee_out(employee) for employee in employees]


@app.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)) -> EmployeeOut:
    regions, skills = _lookup_regions_and_skills(db, payload.region_ids, payload.skill_ids)

    employee = Employee(
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        regions=regions,
        skills=skills,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return _employee_out(employee)


@app.patch("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)
) -> EmployeeOut:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    regions, skills = _lookup_regions_and_skills(db, payload.region_ids, payload.skill_ids)

    employee.name = payload.name
    employee.latitude = payload.latitude
    employee.longitude = payload.longitude
    employee.regions = regions
    employee.skills = skills
    db.commit()
    db.refresh(employee)
    return _employee_out(employee)


@app.delete("/employees/{employee_id}", status_code=204)
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
    "/schedule-templates/{template_id}", response_model=EmployeeScheduleTemplateOut
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


@app.delete("/schedule-templates/{template_id}", status_code=204)
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
    "/schedule-overrides/{override_id}", response_model=EmployeeScheduleDayOverrideOut
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


@app.delete("/schedule-overrides/{override_id}", status_code=204)
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


@app.get("/regions", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)) -> list[Region]:
    return (
        db.query(Region)
        .filter(Region.delete_flag.is_(False))
        .order_by(Region.id)
        .all()
    )


@app.post("/regions", response_model=RegionOut, status_code=201)
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


@app.patch("/regions/{region_id}", response_model=RegionOut)
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


@app.delete("/regions/{region_id}", status_code=204)
def delete_region(region_id: int, db: Session = Depends(get_db)) -> None:
    region = db.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    region.delete_flag = True
    db.commit()


@app.get("/skills", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)) -> list[Skill]:
    return (
        db.query(Skill)
        .filter(Skill.delete_flag.is_(False))
        .order_by(Skill.id)
        .all()
    )


@app.post("/skills", response_model=SkillOut, status_code=201)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)) -> Skill:
    skill = Skill(name=payload.name)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@app.patch("/skills/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: int, payload: SkillUpdate, db: Session = Depends(get_db)) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill.name = payload.name
    db.commit()
    db.refresh(skill)
    return skill


@app.delete("/skills/{skill_id}", status_code=204)
def delete_skill(skill_id: int, db: Session = Depends(get_db)) -> None:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill.delete_flag = True
    db.commit()


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.delete_flag.is_(False))
        .order_by(Customer.id)
        .all()
    )


@app.post("/customers/sync", response_model=list[CustomerOut])
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
        .filter(Customer.delete_flag.is_(False))
        .order_by(Customer.id)
        .all()
    )


@app.get("/customer-locations", response_model=list[CustomerLocationOut])
def list_customer_locations(db: Session = Depends(get_db)) -> list[CustomerLocation]:
    return (
        db.query(CustomerLocation)
        .filter(CustomerLocation.delete_flag.is_(False))
        .options(
            joinedload(CustomerLocation.customer),
            joinedload(CustomerLocation.region),
        )
        .order_by(CustomerLocation.id)
        .all()
    )


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
def list_contracts(db: Session = Depends(get_db)) -> list[ContractOut]:
    contracts = (
        db.query(Contract)
        .filter(Contract.delete_flag.is_(False))
        .options(
            joinedload(Contract.customer),
            joinedload(Contract.lines)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(Contract.lines)
            .joinedload(ContractLine.customer_location)
            .joinedload(CustomerLocation.region),
            joinedload(Contract.lines).joinedload(ContractLine.required_skills),
        )
        .order_by(Contract.id)
        .all()
    )
    return [_contract_out(contract) for contract in contracts]


@app.post("/contracts", response_model=ContractOut, status_code=201)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)) -> ContractOut:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    contract = Contract(customer_id=customer.id)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return _contract_out(contract)


@app.patch("/contracts/{contract_id}", response_model=ContractOut)
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


@app.delete("/contracts/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db)) -> None:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract.delete_flag = True
    for line in contract.lines:
        line.delete_flag = True
    db.commit()


@app.post("/contracts/{contract_id}/lines", response_model=ContractLineOut, status_code=201)
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

    required_skills = db.query(Skill).filter(Skill.id.in_(payload.required_skill_ids)).all()
    if len(required_skills) != len(set(payload.required_skill_ids)):
        raise HTTPException(status_code=404, detail="One or more skills not found")

    line = ContractLine(
        contract_id=contract.id,
        customer_location_id=customer_location.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        interval_days=payload.interval_days,
        duration_minutes=payload.duration_minutes,
        required_skills=required_skills,
    )
    db.add(line)
    db.flush()

    occurrence_dates = generate_occurrence_dates(
        line.start_date, line.interval_days, line.end_date
    )
    for occurrence_date in occurrence_dates:
        db.add(ServiceVisit(contract_line_id=line.id, requested_date=occurrence_date))

    db.commit()
    db.refresh(line)
    return line


@app.patch("/contract-lines/{line_id}", response_model=ContractLineOut)
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

    required_skills = db.query(Skill).filter(Skill.id.in_(payload.required_skill_ids)).all()
    if len(required_skills) != len(set(payload.required_skill_ids)):
        raise HTTPException(status_code=404, detail="One or more skills not found")

    line.customer_location_id = customer_location.id
    line.start_date = payload.start_date
    line.end_date = payload.end_date
    line.interval_days = payload.interval_days
    line.duration_minutes = payload.duration_minutes
    line.required_skills = required_skills
    db.commit()
    db.refresh(line)
    return line


@app.delete("/contract-lines/{line_id}", status_code=204)
def delete_contract_line(line_id: int, db: Session = Depends(get_db)) -> None:
    line = db.get(ContractLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Contract line not found")

    line.delete_flag = True
    db.commit()


@app.get("/service-visits", response_model=list[ServiceVisitOut])
def list_service_visits(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
) -> list[ServiceVisit]:
    query = db.query(ServiceVisit).options(
        joinedload(ServiceVisit.contract_line).joinedload(ContractLine.required_skills),
        joinedload(ServiceVisit.contract_line)
        .joinedload(ContractLine.customer_location)
        .joinedload(CustomerLocation.customer),
        joinedload(ServiceVisit.contract_line)
        .joinedload(ContractLine.customer_location)
        .joinedload(CustomerLocation.region),
    )
    if start_date is not None:
        query = query.filter(ServiceVisit.requested_date >= start_date)
    if end_date is not None:
        query = query.filter(ServiceVisit.requested_date <= end_date)
    return query.order_by(ServiceVisit.id).all()


@app.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)) -> list[Assignment]:
    return (
        db.query(Assignment)
        .options(
            joinedload(Assignment.employee).joinedload(Employee.regions),
            joinedload(Assignment.employee).joinedload(Employee.skills),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract_line)
            .joinedload(ContractLine.required_skills),
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


@app.post("/assignments", response_model=AssignmentOut, status_code=201)
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

    planned_end = payload.planned_start + timedelta(
        minutes=visit.contract_line.duration_minutes
    )
    assignment = Assignment(
        service_visit_id=visit.id,
        employee_id=employee.id,
        planned_start=payload.planned_start,
        planned_end=planned_end,
    )
    visit.status = VisitStatus.ASSIGNED

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@app.delete("/assignments/{service_visit_id}", status_code=204)
def unassign_visit(service_visit_id: int, db: Session = Depends(get_db)) -> None:
    assignment = db.get(Assignment, service_visit_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    visit = assignment.service_visit
    db.delete(assignment)
    visit.status = VisitStatus.UNASSIGNED
    db.commit()


@app.patch("/assignments/{service_visit_id}", response_model=AssignmentOut)
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


@app.post("/optimize/propose", response_model=OptimizationProposal)
def propose_optimization(db: Session = Depends(get_db)) -> OptimizationProposal:
    payload, excluded_visit_ids = build_optimize_payload(db)
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
            joinedload(ServiceVisit.contract_line).joinedload(ContractLine.required_skills),
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
        day_start = datetime.combine(effective_schedule_date(visit), time())
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


@app.post("/optimize/apply", response_model=OptimizationApplyResult)
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

        assignment.employee_id = employee.id
        assignment.planned_start = item.planned_start
        assignment.planned_end = item.planned_start + timedelta(
            minutes=visit.contract_line.duration_minutes
        )
        db.commit()
        db.refresh(assignment)
        results.append(assignment)

    return OptimizationApplyResult(created=results, skipped_visit_ids=skipped)
