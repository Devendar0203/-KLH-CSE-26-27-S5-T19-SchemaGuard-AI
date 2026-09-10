import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import WorkerHealth, ActionLog

def execute_scale_workers(db: Session, decision_id: int, target_worker_count: int = 3) -> dict:
    workers = db.query(WorkerHealth).all()
    existing_count = len(workers)
    
    for i in range(existing_count + 1, target_worker_count + 1):
        name = f"worker_node_{i}"
        w = db.query(WorkerHealth).filter(WorkerHealth.worker_name == name).first()
        if not w:
            db.add(WorkerHealth(
                worker_name=name,
                status="HEALTHY",
                last_heartbeat=datetime.now(timezone.utc),
                restart_count=0
            ))

    result_json = json.dumps({
        "status": "SUCCESS",
        "action": "SCALE_WORKERS",
        "scaled_from": existing_count,
        "scaled_to": target_worker_count
    })

    log = ActionLog(
        decision_id=decision_id,
        action="SCALE_WORKERS",
        status="SUCCESS",
        result_json=result_json,
        executed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    return {"status": "SUCCESS", "message": f"Workers scaled successfully to {target_worker_count} active nodes"}
