from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import PipelineRun, Customer, Quarantine, WorkerHealth
from backend.app.schemas import PipelineStatusResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.get("/status", response_model=PipelineStatusResponse)
def get_pipeline_status(db: Session = Depends(get_db)):
    active_runs = db.query(PipelineRun).filter(PipelineRun.status == "RUNNING").count()
    total_runs = db.query(PipelineRun).count()
    total_records = db.query(Customer).count()
    total_quarantined = db.query(Quarantine).count()

    worker = db.query(WorkerHealth).filter(WorkerHealth.worker_name == "main_worker").first()
    worker_health_status = worker.status if worker else "HEALTHY"

    system_health = "HEALTHY"
    if total_quarantined > 0:
        system_health = "DEGRADED"

    return PipelineStatusResponse(
        active_runs=active_runs,
        total_runs=total_runs,
        total_records=total_records,
        total_quarantined=total_quarantined,
        worker_health_status=worker_health_status,
        system_health=system_health
    )
