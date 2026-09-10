import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, SessionLocal, Base
from monitoring.health_monitor import HealthMonitor
from ai_engine.schema_matcher import SchemaMatcher
from ai_engine.anomaly_detector import AnomalyDetector
from ai_engine.failure_classifier import FailureClassifier

def test_phase2():
    print("==================================================")
    print("  PHASE 2 VERIFICATION: MONITORING & AI DETECTION ")
    print("==================================================")

    # Init DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    monitor = HealthMonitor(db)
    matcher = SchemaMatcher(use_embeddings=True)
    detector = AnomalyDetector()
    classifier = FailureClassifier()

    # 1. Test Schema Matcher (Semantic Similarity)
    print("\n[1/4] Testing Schema Matcher (sentence-transformers / embedding similarity)...")
    res_match = matcher.find_best_match(
        unexpected_field="customerId",
        expected_fields=["customer_id", "first_name", "last_name", "email", "account_balance"]
    )
    print(f"  Field Match Result: 'customerId' -> '{res_match['mapped_to_field']}' (Confidence: {res_match['confidence']})")
    assert res_match['mapped_to_field'] == "customer_id", "Schema matcher failed to map customerId to customer_id!"
    assert res_match['confidence'] >= 0.70, "Confidence score too low!"

    # 2. Test Anomaly Detector (Isolation Forest)
    print("\n[2/4] Testing Anomaly Detector (Isolation Forest on metric windows)...")
    normal_res = detector.detect(record_count=5, error_rate=0.0, latency_ms=45.0, quarantine_rate=0.0)
    print(f"  Normal Batch Metric Evaluation: Anomaly={normal_res['is_anomaly']}, Score={normal_res['anomaly_score']}")
    
    spike_res = detector.detect(record_count=150, error_rate=0.4, latency_ms=850.0, quarantine_rate=0.3)
    print(f"  Spike Batch Metric Evaluation: Anomaly={spike_res['is_anomaly']}, Score={spike_res['anomaly_score']}")
    assert spike_res['is_anomaly'] == True, "Anomaly detector failed to flag workload spike!"

    # 3. Test Worker & Health Probes
    print("\n[3/4] Testing Worker Health Monitoring Probes...")
    monitor.heartbeat_worker("main_worker", "HEALTHY")
    status_healthy = monitor.get_worker_status("main_worker")
    print(f"  Worker Status: {status_healthy['status']} (Is Alive: {status_healthy['is_alive']})")

    # 4. Test Failure Classifier
    print("\n[4/4] Testing Failure Classifier (Event Classification)...")
    test_cases = [
        {
            "name": "Schema Drift Scenario",
            "evidence": {
                "schema_diff": {"missing_fields": ["customer_id"], "unexpected_fields": ["customerId"]},
                "schema_match": res_match
            },
            "expected_event": "schema_drift"
        },
        {
            "name": "Worker Failure Scenario",
            "evidence": {"worker_status": "CRASHED"},
            "expected_event": "worker_crash"
        },
        {
            "name": "Workload Spike Scenario",
            "evidence": {"record_count": 50, "anomaly_score": 0.85},
            "expected_event": "workload_spike"
        },
        {
            "name": "Database Failure Scenario",
            "evidence": {"db_status": "UNREACHABLE"},
            "expected_event": "db_outage"
        }
    ]

    for tc in test_cases:
        cls_res = classifier.classify(tc["evidence"])
        print(f"  {tc['name']} -> Event: '{cls_res['event_type']}', Severity: {cls_res['severity']}, Confidence: {cls_res['confidence']}")
        print(f"    Rationale: {cls_res['rationale']}")
        assert cls_res['event_type'] == tc['expected_event'], f"Failed classifying {tc['name']}!"

    db.close()
    print("\n==================================================")
    print("  PHASE 2 VERIFICATION SUCCESSFUL!                ")
    print("==================================================")

if __name__ == "__main__":
    test_phase2()
