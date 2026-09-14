from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Assignment, ServiceVisit, VisitStatus


def refresh_demo_schedule(db: Session) -> dict:
    """Shift every service visit's requested_date forward just enough that
    the earliest becomes today - preserving each visit's spacing relative to
    every other one - and clear every assignment (pinned or not) back to
    unassigned. Local-only: no Tripletex calls, no changes to customers,
    customer locations, contracts, contract lines, or employees.
    """
    earliest = db.query(func.min(ServiceVisit.requested_date)).scalar()
    days_shifted = 0
    if earliest is not None:
        days_shifted = max(0, (date.today() - earliest).days)
        if days_shifted > 0:
            db.query(ServiceVisit).update(
                {ServiceVisit.requested_date: ServiceVisit.requested_date + timedelta(days=days_shifted)},
                synchronize_session=False,
            )

    visits_unassigned = (
        db.query(ServiceVisit)
        .filter(ServiceVisit.status == VisitStatus.ASSIGNED)
        .update({ServiceVisit.status: VisitStatus.UNASSIGNED}, synchronize_session=False)
    )
    db.query(Assignment).delete(synchronize_session=False)

    db.commit()
    return {"days_shifted": days_shifted, "visits_unassigned": visits_unassigned}
