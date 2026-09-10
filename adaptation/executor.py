from sqlalchemy.orm import Session
from adaptation.map_schema import execute_map_schema, rollback_map_schema
from adaptation.quarantine_data import execute_quarantine_data
from adaptation.restart_worker import execute_restart_worker
from adaptation.buffer_failover import execute_buffer_records, flush_buffer
from adaptation.scale_workers import execute_scale_workers

class ActionExecutor:
    def __init__(self, db: Session):
        self.db = db

    def execute_action(self, decision_id: int, action: str, params: dict) -> dict:
        if action == "MAP_SCHEMA":
            return execute_map_schema(
                self.db,
                decision_id=decision_id,
                source_name=params.get("source_name", "customers_csv"),
                original_field=params.get("original_field", "customerId"),
                target_field=params.get("target_field", "customer_id"),
                confidence=params.get("confidence", 0.95)
            )
        elif action == "QUARANTINE_DATA":
            return execute_quarantine_data(
                self.db,
                decision_id=decision_id,
                run_id=params.get("run_id", 0),
                records=params.get("records", []),
                reason=params.get("reason", "Data quality check failure")
            )
        elif action == "RESTART_WORKER":
            return execute_restart_worker(
                self.db,
                decision_id=decision_id,
                worker_name=params.get("worker_name", "main_worker")
            )
        elif action == "BUFFER" or action == "RETRY":
            return execute_buffer_records(
                self.db,
                decision_id=decision_id,
                records=params.get("records", [])
            )
        elif action == "SCALE_WORKERS":
            return execute_scale_workers(
                self.db,
                decision_id=decision_id,
                target_worker_count=params.get("target_worker_count", 3)
            )
        else:
            raise ValueError(f"Unknown or unauthorized action: {action}")
