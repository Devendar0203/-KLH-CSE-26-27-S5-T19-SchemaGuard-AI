from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import IngestBatchRequest, IngestBatchResponse
from backend.app.services.ingestion_service import process_ingest_batch

router = APIRouter(prefix="", tags=["Ingest"])

@router.post("/ingest", response_model=IngestBatchResponse)
def ingest_data(batch: IngestBatchRequest, db: Session = Depends(get_db)):
    if not batch.records:
        raise HTTPException(status_code=400, detail="Empty batch records")

    result = process_ingest_batch(db, batch.source_name, batch.dag_run_id, batch.records)
    return IngestBatchResponse(
        run_id=result["run_id"],
        status=result["status"],
        processed_count=result["processed_count"],
        quarantined_count=result["quarantined_count"]
    )
