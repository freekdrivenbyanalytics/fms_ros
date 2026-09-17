"""One-time script: create the demo Skill/ServiceOrderType records, assign
them to the 4 existing demo products, reassign the contract lines that used
to require TJN10004 over to TJN10010, and set the 3 active employees' skills.

Not part of seed.py or backend startup - run manually, once, from the
backend directory:

    .venv/Scripts/python.exe scripts/assign_skills_and_service_order_types.py

Skill/ServiceOrderType associations are local-only (never pushed to
Tripletex/Resco - see openspec/changes/archive/*add-skills-and-service-order-types*
design.md), so this script only touches the local database; no Tripletex or
Resco API calls are made.
"""

from app.database import SessionLocal
from app.models import ContractLine, Employee, Product, ServiceOrderType, Skill

GENERAL_PRODUCT_NUMBERS = ["TJN10001", "TJN10002", "TJN10003"]
WINTER_PRODUCT_NUMBER = "TJN10010"
DISPLACED_PRODUCT_NUMBER = "TJN10004"

SKILL_INSPECTION = "Inspeksjon (vaktmester)"
SKILL_SNOW_CLEARING = "Snømåking"

SERVICE_ORDER_TYPE_GENERAL = "Generelle vaktmestertjenester"
SERVICE_ORDER_TYPE_WINTER = "Vaktmestertjenester (vinter)"


def _get_or_create_skill(db, name: str) -> Skill:
    skill = db.query(Skill).filter(Skill.name == name).first()
    if skill is None:
        skill = Skill(name=name)
        db.add(skill)
        db.flush()
    return skill


def _get_or_create_service_order_type(db, name: str) -> ServiceOrderType:
    service_order_type = db.query(ServiceOrderType).filter(ServiceOrderType.name == name).first()
    if service_order_type is None:
        service_order_type = ServiceOrderType(name=name)
        db.add(service_order_type)
        db.flush()
    return service_order_type


def main() -> None:
    db = SessionLocal()
    try:
        inspection = _get_or_create_skill(db, SKILL_INSPECTION)
        snow_clearing = _get_or_create_skill(db, SKILL_SNOW_CLEARING)
        general_type = _get_or_create_service_order_type(db, SERVICE_ORDER_TYPE_GENERAL)
        winter_type = _get_or_create_service_order_type(db, SERVICE_ORDER_TYPE_WINTER)

        general_products = (
            db.query(Product).filter(Product.number.in_(GENERAL_PRODUCT_NUMBERS)).all()
        )
        if len(general_products) != len(GENERAL_PRODUCT_NUMBERS):
            found = {p.number for p in general_products}
            missing = set(GENERAL_PRODUCT_NUMBERS) - found
            raise RuntimeError(f"Missing expected product(s): {sorted(missing)}")
        for product in general_products:
            product.skills = [inspection]
            product.service_order_type = general_type

        winter_product = db.query(Product).filter(Product.number == WINTER_PRODUCT_NUMBER).first()
        if winter_product is None:
            raise RuntimeError(f"Missing expected product: {WINTER_PRODUCT_NUMBER}")
        winter_product.skills = [inspection, snow_clearing]
        winter_product.service_order_type = winter_type

        displaced_product = (
            db.query(Product).filter(Product.number == DISPLACED_PRODUCT_NUMBER).first()
        )
        reassigned_lines = 0
        if displaced_product is not None:
            lines = (
                db.query(ContractLine)
                .filter(ContractLine.required_products.contains(displaced_product))
                .all()
            )
            for line in lines:
                line.required_products = [
                    winter_product if p.id == displaced_product.id else p
                    for p in line.required_products
                ]
                reassigned_lines += 1

        employees = db.query(Employee).filter(Employee.delete_flag.is_(False)).order_by(Employee.id).all()
        if not employees:
            raise RuntimeError("No active employees found")
        for employee in employees[:-1]:
            employee.skills = [inspection, snow_clearing]
        employees[-1].skills = [inspection]

        db.commit()

        print(f"Skills: {inspection.name!r}, {snow_clearing.name!r}")
        print(f"Service order types: {general_type.name!r}, {winter_type.name!r}")
        print(
            f"General products ({', '.join(GENERAL_PRODUCT_NUMBERS)}): "
            f"service order type={general_type.name!r}, skills=[{inspection.name!r}]"
        )
        print(
            f"Winter product ({WINTER_PRODUCT_NUMBER}): "
            f"service order type={winter_type.name!r}, skills=[{inspection.name!r}, {snow_clearing.name!r}]"
        )
        print(f"Reassigned {reassigned_lines} contract line(s) from {DISPLACED_PRODUCT_NUMBER} to {WINTER_PRODUCT_NUMBER}")
        for employee in employees[:-1]:
            print(f"  {employee.name}: {[s.name for s in employee.skills]}")
        print(f"  {employees[-1].name}: {[s.name for s in employees[-1].skills]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
