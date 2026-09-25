"""One-time, local-only caretaker task setup. Safe to rerun after administrator edits."""
from sqlalchemy import text

from app.database import SessionLocal
from app.models import RescoSyncRecord, ServiceOrderType, ServiceOrderTypeTask, Task


def seed_tasks(db):
    db.execute(text("SELECT pg_advisory_xact_lock(7281940029)"))
    key = "seed:caretaker-tasks-v1"
    if db.get(RescoSyncRecord, key):
        return False
    names = ["Generelle vaktmestertjenester", "Vaktmestertjenester (vinter)"]
    types = []
    for name in names:
        matches = db.query(ServiceOrderType).filter_by(name=name, delete_flag=False).all()
        if len(matches) != 1:
            raise ValueError(f"Expected one active service order type named {name!r}, found {len(matches)}")
        types.append(matches[0])
    tasks = []
    for name in ("generell inspeksjon", "lett snømåking"):
        matches = db.query(Task).filter_by(name=name, delete_flag=False).all()
        if len(matches) > 1:
            raise ValueError(f"Ambiguous task name {name!r}")
        task = matches[0] if matches else Task(name=name)
        db.add(task)
        db.flush()
        tasks.append(task)
    for type_, wanted in ((types[0], tasks[:1]), (types[1], tasks)):
        links = {link.task_id: link for link in type_.task_links}
        pos = max((link.position for link in links.values()), default=-1) + 1
        for task in wanted:
            if task.id not in links:
                db.add(ServiceOrderTypeTask(service_order_type_id=type_.id,
                                             task_id=task.id, position=pos))
                pos += 1
    db.add(RescoSyncRecord(key=key, entity="local-seed", remote_id="none", payload={}, completed=True))
    db.flush()
    return True


if __name__ == "__main__":
    with SessionLocal.begin() as db:
        print("Initial tasks added" if seed_tasks(db) else "Initial tasks already populated")
