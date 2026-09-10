import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, SessionLocal, Base
from backend.app.models import Event, Decision, ActionLog, ActiveSchemaMapping, WorkerHealth
from ai_engine.decision_engine import DecisionEngine

def test_phase3():
    print("==================================================")
    print("  PHASE 3 VERIFICATION: DECISION & ADAPTATION     ")
    print("==================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    engine_inst = DecisionEngine(db)

    # 1. Test Auto-Execution for Schema Drift -> MAP_SCHEMA
    print("\n[1/3] Testing Decision Engine Auto-Execution (schema_drift -> MAP_SCHEMA)...")
    classification_drift = {
        "event_type": "schema_drift",
        "severity": "MEDIUM",
        "confidence": 0.95,
        "rationale": "Detected schema mismatch. Field 'customerId' semantically matches 'customer_id' with 0.95 confidence.",
        "evidence": {
            "schema_match": {
                "unexpected_field": "customerId",
                "mapped_to_field": "customer_id",
                "confidence": 0.95
            }
        }
    }
    res_drift = engine_inst.process_classified_event(run_id=1, classification=classification_drift, params={"source_name": "customers_csv"})
    print(f"  Decision Result: ChosenAction='{res_drift['chosen_action']}', Status='{res_drift['status']}'")
    print(f"  Execution Message: {res_drift['execution_result']}")
    assert res_drift["chosen_action"] == "MAP_SCHEMA"
    assert res_drift["status"] == "EXECUTED"
    
    # Verify active schema mapping created in DB
    mapping = db.query(ActiveSchemaMapping).filter(ActiveSchemaMapping.original_field == "customerId").first()
    assert mapping is not None and mapping.target_field == "customer_id", "MAP_SCHEMA failed to update database!"

    # 2. Test Auto-Execution for Worker Crash -> RESTART_WORKER
    print("\n[2/3] Testing Decision Engine Auto-Execution (worker_crash -> RESTART_WORKER)...")
    classification_worker = {
        "event_type": "worker_crash",
        "severity": "HIGH",
        "confidence": 0.92,
        "rationale": "Worker node heartbeat expired.",
        "evidence": {"worker_status": "CRASHED"}
    }
    res_worker = engine_inst.process_classified_event(run_id=1, classification=classification_worker)
    print(f"  Decision Result: ChosenAction='{res_worker['chosen_action']}', Status='{res_worker['status']}'")
    print(f"  Execution Message: {res_worker['execution_result']}")
    assert res_worker["chosen_action"] == "RESTART_WORKER"

    # Verify worker node restored to HEALTHY
    w = db.query(WorkerHealth).filter(WorkerHealth.worker_name == "main_worker").first()
    assert w is not None and w.status == "HEALTHY", "Worker status was not restored to HEALTHY!"

    # 3. Test Low Confidence -> HUMAN_APPROVAL & Manual Override
    print("\n[3/3] Testing Low Confidence routing to HUMAN_APPROVAL & Manual Approval Flow...")
    classification_uncertain = {
        "event_type": "workload_spike",
        "severity": "HIGH",
        "confidence": 0.65, # Below 0.80 threshold
        "rationale": "High throughput burst observed, but system confidence is low.",
        "evidence": {"record_count": 80}
    }
    res_human = engine_inst.process_classified_event(run_id=1, classification=classification_uncertain)
    print(f"  Uncertain Event Decision Result: ChosenAction='{res_human['chosen_action']}', Status='{res_human['status']}'")
    assert res_human["chosen_action"] == "HUMAN_APPROVAL"
    assert res_human["status"] == "PENDING_APPROVAL"

    # Simulate Human Approving decision
    print(f"  Simulating Human Approving Decision ID #{res_human['decision_id']}...")
    approve_res = engine_inst.approve_human_decision(decision_id=res_human['decision_id'], params={"target_worker_count": 3})
    print(f"  Human Approval Result: Status='{approve_res['status']}', ActionExecuted='{approve_res['action']}'")
    assert approve_res["status"] == "APPROVED_AND_EXECUTED"

    # Verify Actions Log
    log_count = db.query(ActionLog).count()
    print(f"\nTotal Action Log Entries recorded in DB: {log_count}")
    assert log_count >= 3, "Actions log entry count lower than expected!"

    db.close()
    print("\n==================================================")
    print("  PHASE 3 VERIFICATION SUCCESSFUL!                ")
    print("==================================================")

if __name__ == "__main__":
    test_phase3()
