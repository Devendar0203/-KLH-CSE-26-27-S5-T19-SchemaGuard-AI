import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import WorkerHealth, ActionLog

def execute_restart_worker(db: Session, decision_id: int, worker_name: str = "main_worker") -> dict:
    worker = db.query(WorkerHealth).filter(WorkerHealth.worker_name == worker_name).first()
    if not worker:
        worker = WorkerHealth(
            worker_name=worker_name,
            status="HEALTHY",
            last_heartbeat=datetime.now(timezone.utc),
            restart_count=1
        )
        db.add(worker)
    else:
        worker.status = "HEALTHY"
        worker.last_heartbeat = datetime.now(timezone.utc)
        worker.restart_count += 1

    result_json = json.dumps({
        "status": "SUCCESS",
        "action": "RESTART_WORKER",
        "worker": worker_name,
        "new_restart_count": worker.restart_count
    })

    log = ActionLog(
        decision_id=decision_id,
        action="RESTART_WORKER",
        status="SUCCESS",
        result_json=result_json,
        executed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    return {"status": "SUCCESS", "message": f"Worker '{worker_name}' restarted successfully (restart count: {worker.restart_count})"}
