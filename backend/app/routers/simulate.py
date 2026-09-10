from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import WorkerHealth
from monitoring.health_monitor import HealthMonitor
from ai_engine.schema_matcher import SchemaMatcher
from ai_engine.anomaly_detector import AnomalyDetector
from ai_engine.failure_classifier import FailureClassifier
from ai_engine.decision_engine import DecisionEngine
from backend.app.services.ingestion_service import process_ingest_batch
from backend.app.services.knowledge_service import validate_and_record_knowledge
from backend.app.schemas import FaultSimulationRequest

router = APIRouter(prefix="", tags=["Simulation"])

@router.post("/simulate/fault")
def simulate_fault(req: FaultSimulationRequest, db: Session = Depends(get_db)):
    fault_type = req.fault_type.lower()
    source_name = req.source_name or "customers_csv"

    monitor = HealthMonitor(db)
    matcher = SchemaMatcher()
    detector = AnomalyDetector()
    classifier = FailureClassifier()
    decision_eng = DecisionEngine(db)

    run_id = 0
    classification = None
    params = {"source_name": source_name}

    if fault_type == "schema_drift":
        # Simulate incoming batch with drifted column header: customer_id -> customerId
        drifted_records = [
            {"customerId": "CUST-9001", "first_name": "DriftAlice", "last_name": "Test", "email": "drift@example.com", "signup_date": "2026-03-01", "account_balance": 1500.0}
        ]
        fp = monitor.inspect_schema_fingerprint(source_name, ["customerId", "first_name", "last_name", "email", "signup_date", "account_balance"])
        sm = matcher.find_best_match("customerId", ["customer_id", "first_name", "last_name", "email", "account_balance"])
        
        evidence = {
            "schema_diff": {"missing_fields": fp["missing_fields"], "unexpected_fields": fp["unexpected_fields"]},
            "schema_match": sm
        }
        classification = classifier.classify(evidence)

    elif fault_type == "bad_data":
        # Simulate batch with invalid account_balance format / missing required fields
        bad_records = [
            {"customer_id": "CUST-BAD1", "first_name": "Invalid", "last_name": "Data", "email": "bad@example.com", "account_balance": "INVALID_NUMBER"}
        ]
        res_ingest = process_ingest_batch(db, source_name, "sim_bad_data", bad_records)
        run_id = res_ingest["run_id"]
        evidence = {
            "quarantine_count": res_ingest["quarantined_count"],
            "processed_count": res_ingest["processed_count"]
        }
        classification = classifier.classify(evidence)

    elif fault_type == "worker_crash":
        # Set main worker status to CRASHED
        monitor.heartbeat_worker("main_worker", "CRASHED")
        ws = monitor.get_worker_status("main_worker")
        evidence = {"worker_status": ws["status"]}
        classification = classifier.classify(evidence)

    elif fault_type == "db_outage":
        evidence = {"db_status": "UNREACHABLE"}
        classification = classifier.classify(evidence)
        params["records"] = [{"customer_id": "CUST-BUF1", "first_name": "BufferRecord", "last_name": "Saved"}]

    elif fault_type == "workload_spike":
        # Simulate burst batch
        eval_res = detector.detect(record_count=120, error_rate=0.05, latency_ms=650.0, quarantine_rate=0.0)
        evidence = {
            "record_count": 120,
            "anomaly_score": eval_res["anomaly_score"],
            "is_anomaly": eval_res["is_anomaly"]
        }
        classification = classifier.classify(evidence)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported fault type: {fault_type}")

    # Process via Decision Engine
    decision_outcome = decision_eng.process_classified_event(run_id, classification, params)

    # Validate and record Knowledge Base entry if executed
    if decision_outcome.get("status") in ("EXECUTED", "SUCCESS"):
        action = decision_outcome.get("chosen_action")
        validate_and_record_knowledge(db, fault_type, action, decision_outcome.get("rationale", ""))

    return {
        "fault_type": fault_type,
        "classification": classification,
        "decision": decision_outcome
    }
