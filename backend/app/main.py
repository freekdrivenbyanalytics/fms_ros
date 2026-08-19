from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Assignment, Employee, ServiceVisit, VisitStatus
from app.schemas import AssignmentCreate, AssignmentOut, EmployeeOut, ServiceVisitOut

app = FastAPI(title="fms_ros")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)) -> list[Employee]:
    return db.query(Employee).order_by(Employee.id).all()


@app.get("/service-visits", response_model=list[ServiceVisitOut])
def list_service_visits(db: Session = Depends(get_db)) -> list[ServiceVisit]:
    return db.query(ServiceVisit).order_by(ServiceVisit.id).all()


@app.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)) -> list[Assignment]:
    return (
        db.query(Assignment)
        .options(joinedload(Assignment.employee), joinedload(Assignment.service_visit))
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

    planned_end = payload.planned_start + timedelta(minutes=visit.duration_minutes)
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
