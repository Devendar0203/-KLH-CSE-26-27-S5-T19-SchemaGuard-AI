from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class IngestBatchRequest(BaseModel):
    source_name: str
    dag_run_id: Optional[str] = "manual_run"
    records: List[Dict[str, Any]]

class IngestBatchResponse(BaseModel):
    run_id: int
    status: str
    processed_count: int
    quarantined_count: int
    events_triggered: List[str] = []

class PipelineStatusResponse(BaseModel):
    active_runs: int
    total_runs: int
    total_records: int
    total_quarantined: int
    worker_health_status: str
    system_health: str # HEALTHY, DEGRADED, RECOVERING

class FaultSimulationRequest(BaseModel):
    fault_type: str # schema_drift | bad_data | worker_crash | db_outage | workload_spike
    source_name: Optional[str] = "customers_csv"
