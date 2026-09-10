from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.models import WorkerHealth, SchemaVersion, PipelineRun, Quarantine

class HealthMonitor:
    def __init__(self, db: Session):
        self.db = db

    def heartbeat_worker(self, worker_name: str = "main_worker", status: str = "HEALTHY"):
        worker = self.db.query(WorkerHealth).filter(WorkerHealth.worker_name == worker_name).first()
        if not worker:
            worker = WorkerHealth(
                worker_name=worker_name,
                status=status,
                last_heartbeat=datetime.now(timezone.utc),
                restart_count=0
            )
            self.db.add(worker)
        else:
            worker.status = status
            worker.last_heartbeat = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(worker)
        return worker

    def get_worker_status(self, worker_name: str = "main_worker") -> dict:
        worker = self.db.query(WorkerHealth).filter(WorkerHealth.worker_name == worker_name).first()
        if not worker:
            return {"status": "UNKNOWN", "is_alive": False, "restart_count": 0}
        
        # Consider worker dead if heartbeat older than 15 seconds
        is_alive = (datetime.now(timezone.utc) - worker.last_heartbeat.replace(tzinfo=timezone.utc if worker.last_heartbeat.tzinfo is None else worker.last_heartbeat)) < timedelta(seconds=15)
        status = worker.status if is_alive else "CRASHED"
        return {
            "status": status,
            "is_alive": is_alive,
            "last_heartbeat": worker.last_heartbeat.isoformat(),
            "restart_count": worker.restart_count
        }

    def inspect_schema_fingerprint(self, source_name: str, incoming_fields: list) -> dict:
        known_schemas = self.db.query(SchemaVersion).filter(SchemaVersion.source_name == source_name).all()
        expected_fields = set(s.field_name for s in known_schemas)
        
        incoming_set = set(incoming_fields)
        missing_fields = list(expected_fields - incoming_set)
        unexpected_fields = list(incoming_set - expected_fields)
        
        return {
            "expected_fields": list(expected_fields),
            "incoming_fields": incoming_fields,
            "missing_fields": missing_fields,
            "unexpected_fields": unexpected_fields,
            "has_drift": len(missing_fields) > 0 or len(unexpected_fields) > 0
        }
