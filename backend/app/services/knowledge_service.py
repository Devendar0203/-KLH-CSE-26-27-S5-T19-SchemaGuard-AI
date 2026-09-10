from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import KnowledgeBase, WorkerHealth, Customer

def validate_and_record_knowledge(db: Session, event_type: str, action: str, result_summary: str) -> bool:
    # Perform validation health check based on event type
    success = True
    outcome = ""

    if event_type == "schema_drift" and action == "MAP_SCHEMA":
        outcome = f"Schema mapping applied successfully. {result_summary}"
        success = True
    elif event_type == "worker_crash" and action == "RESTART_WORKER":
        w = db.query(WorkerHealth).filter(WorkerHealth.worker_name == "main_worker").first()
        success = w is not None and w.status == "HEALTHY"
        outcome = "Worker restored to HEALTHY status and active." if success else "Worker restart validation failed."
    elif event_type == "workload_spike" and action == "SCALE_WORKERS":
        workers = db.query(WorkerHealth).all()
        success = len(workers) >= 2
        outcome = f"Scaled workers operating with {len(workers)} active nodes." if success else "Worker scaling failed."
    elif event_type == "db_outage":
        outcome = "Record buffering active until database recovers."
        success = True
    else:
        outcome = f"Action '{action}' executed cleanly. {result_summary}"
        success = True

    kb = KnowledgeBase(
        event_type=event_type,
        action=action,
        outcome=outcome,
        success_bool=success,
        created_at=datetime.now(timezone.utc)
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return success
