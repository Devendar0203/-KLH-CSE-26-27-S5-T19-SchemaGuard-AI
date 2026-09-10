from typing import Dict, Any

class FailureClassifier:
    def classify(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input evidence dict structure:
        {
            "schema_diff": {"missing_fields": [...], "unexpected_fields": [...]},
            "schema_match": {"mapped_to_field": ..., "confidence": ...},
            "quarantine_count": int,
            "worker_status": str,
            "db_status": str,
            "record_count": int,
            "anomaly_score": float
        }
        """
        schema_diff = evidence.get("schema_diff", {})
        schema_match = evidence.get("schema_match")
        quarantine_count = evidence.get("quarantine_count", 0)
        worker_status = evidence.get("worker_status", "HEALTHY")
        db_status = evidence.get("db_status", "CONNECTED")
        record_count = evidence.get("record_count", 0)
        anomaly_score = evidence.get("anomaly_score", 0.0)

        # 1. Check DB Outage
        if db_status in ("UNREACHABLE", "DISCONNECTED", "TIMEOUT"):
            return {
                "event_type": "db_outage",
                "severity": "CRITICAL",
                "confidence": 0.98,
                "rationale": f"Database status reported as {db_status}. Ingestion operations blocked.",
                "evidence": evidence
            }

        # 2. Check Worker Failure
        if worker_status in ("CRASHED", "STOPPED", "DEAD"):
            return {
                "event_type": "worker_crash",
                "severity": "HIGH",
                "confidence": 0.95,
                "rationale": f"Pipeline worker node status is '{worker_status}'. Heartbeat expired.",
                "evidence": evidence
            }

        # 3. Check Schema Drift
        if schema_diff.get("missing_fields") or schema_diff.get("unexpected_fields"):
            unexp = schema_diff.get("unexpected_fields", [])
            miss = schema_diff.get("missing_fields", [])
            match_str = ""
            confidence = 0.92
            if schema_match:
                match_str = f" Semantic match found: '{schema_match.get('unexpected_field')}' -> '{schema_match.get('mapped_to_field')}' (similarity: {schema_match.get('confidence'):.2f})."
                confidence = max(confidence, schema_match.get("confidence", 0.90))

            return {
                "event_type": "schema_drift",
                "severity": "MEDIUM",
                "confidence": round(confidence, 2),
                "rationale": f"Detected schema mismatch. Unexpected fields: {unexp}, Missing fields: {miss}.{match_str}",
                "evidence": evidence
            }

        # 4. Check Workload Spike
        if record_count >= 30 or anomaly_score >= 0.70:
            return {
                "event_type": "workload_spike",
                "severity": "MEDIUM",
                "confidence": 0.88,
                "rationale": f"High ingestion volume detected ({record_count} records in batch, anomaly index: {anomaly_score:.2f}). Worker throughput capacity exceeded.",
                "evidence": evidence
            }

        # 5. Check Bad / Invalid Data
        if quarantine_count > 0:
            return {
                "event_type": "bad_data",
                "severity": "LOW",
                "confidence": 0.90,
                "rationale": f"Found {quarantine_count} invalid records violating field format constraints.",
                "evidence": evidence
            }

        return {
            "event_type": "none",
            "severity": "NONE",
            "confidence": 1.0,
            "rationale": "All metrics and schemas within normal operating thresholds.",
            "evidence": evidence
        }
