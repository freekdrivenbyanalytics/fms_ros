import logging
from contextlib import asynccontextmanager
from datetime import datetime, time, timedelta

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal, get_db
from app.models import (
    Assignment,
    Contract,
    Customer,
    CustomerLocation,
    Employee,
    Region,
    ServiceVisit,
    Skill,
    VisitStatus,
)
from app.schemas import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentPinUpdate,
    ContractOut,
    CustomerLocationOut,
    CustomerOut,
    EmployeeOut,
    OptimizationApplyRequest,
    OptimizationApplyResult,
    OptimizationProposal,
    ProposedAssignmentOut,
    RegionOut,
    ServiceVisitOut,
    SkillOut,
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


@app.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)) -> list[Employee]:
    return (
        db.query(Employee)
        .options(joinedload(Employee.regions), joinedload(Employee.skills))
        .order_by(Employee.id)
        .all()
    )


@app.get("/regions", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)) -> list[Region]:
    return db.query(Region).order_by(Region.id).all()


@app.get("/skills", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)) -> list[Skill]:
    return db.query(Skill).order_by(Skill.id).all()


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


@app.get("/contracts", response_model=list[ContractOut])
def list_contracts(db: Session = Depends(get_db)) -> list[Contract]:
    return (
        db.query(Contract)
        .options(
            joinedload(Contract.customer_location).joinedload(CustomerLocation.customer),
            joinedload(Contract.customer_location).joinedload(CustomerLocation.region),
            joinedload(Contract.required_skills),
        )
        .order_by(Contract.id)
        .all()
    )


@app.get("/service-visits", response_model=list[ServiceVisitOut])
def list_service_visits(db: Session = Depends(get_db)) -> list[ServiceVisit]:
    return (
        db.query(ServiceVisit)
        .options(
            joinedload(ServiceVisit.contract).joinedload(Contract.required_skills),
            joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
            .joinedload(CustomerLocation.region),
        )
        .order_by(ServiceVisit.id)
        .all()
    )


@app.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)) -> list[Assignment]:
    return (
        db.query(Assignment)
        .options(
            joinedload(Assignment.employee).joinedload(Employee.regions),
            joinedload(Assignment.employee).joinedload(Employee.skills),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract)
            .joinedload(Contract.required_skills),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(Assignment.service_visit)
            .joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
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
        minutes=visit.contract.duration_minutes
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
            joinedload(ServiceVisit.contract).joinedload(Contract.required_skills),
            joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
            .joinedload(CustomerLocation.customer),
            joinedload(ServiceVisit.contract)
            .joinedload(Contract.customer_location)
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
            minutes=visit.contract.duration_minutes
        )
        db.commit()
        db.refresh(assignment)
        results.append(assignment)

    return OptimizationApplyResult(created=results, skipped_visit_ids=skipped)
