import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import Event, Decision
from adaptation.executor import ActionExecutor

class DecisionEngine:
    # Fixed Approved Action Registry
    ACTION_REGISTRY = {
        "schema_drift": "MAP_SCHEMA",
        "bad_data": "QUARANTINE_DATA",
        "worker_crash": "RESTART_WORKER",
        "db_outage": "BUFFER",
        "workload_spike": "SCALE_WORKERS"
    }

    CONFIDENCE_THRESHOLD = 0.80

    def __init__(self, db: Session):
        self.db = db
        self.executor = ActionExecutor(db)

    def process_classified_event(self, run_id: int, classification: dict, params: dict = None) -> dict:
        if params is None:
            params = {}

        event_type = classification.get("event_type", "none")
        severity = classification.get("severity", "LOW")
        confidence = classification.get("confidence", 0.0)
        rationale = classification.get("rationale", "")
        evidence = classification.get("evidence", {})

        if event_type == "none":
            return {"status": "NO_ACTION_REQUIRED"}

        # 1. Log Event
        event = Event(
            run_id=run_id,
            event_type=event_type,
            severity=severity,
            detected_at=datetime.now(timezone.utc),
            evidence_json=json.dumps(evidence)
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # 2. Pick Action from Registry
        target_action = self.ACTION_REGISTRY.get(event_type, "HUMAN_APPROVAL")

        # 3. Check Confidence Threshold Constraint
        requires_human = confidence < self.CONFIDENCE_THRESHOLD or params.get("force_human_approval", False)

        chosen_action = "HUMAN_APPROVAL" if requires_human else target_action
        decision_status = "PENDING_APPROVAL" if requires_human else "EXECUTED"

        # 4. Log Decision
        decision = Decision(
            event_id=event.id,
            chosen_action=chosen_action,
            confidence=confidence,
            rationale=f"AI Decision ({'Auto-Execute' if not requires_human else 'Requires Human Approval'}): {rationale} [Proposed Action: {target_action}]",
            decided_at=datetime.now(timezone.utc),
            status=decision_status
        )
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)

        # 5. Execute Action if Auto-Approved
        execution_result = None
        if not requires_human:
            # Add parameters from classification / evidence
            if event_type == "schema_drift":
                sm = classification.get("evidence", {}).get("schema_match", {})
                params["source_name"] = params.get("source_name", "customers_csv")
                params["original_field"] = sm.get("unexpected_field", "customerId")
                params["target_field"] = sm.get("mapped_to_field", "customer_id")
                params["confidence"] = confidence

            execution_result = self.executor.execute_action(decision.id, target_action, params)

        return {
            "event_id": event.id,
            "decision_id": decision.id,
            "event_type": event_type,
            "chosen_action": chosen_action,
            "proposed_action": target_action,
            "status": decision_status,
            "confidence": confidence,
            "rationale": decision.rationale,
            "execution_result": execution_result
        }

    def approve_human_decision(self, decision_id: int, params: dict = None) -> dict:
        if params is None:
            params = {}

        decision = self.db.query(Decision).filter(Decision.id == decision_id).first()
        if not decision or decision.status != "PENDING_APPROVAL":
            raise ValueError(f"Decision {decision_id} is not pending human approval.")

        # Determine target action from rationale or event
        event = self.db.query(Event).filter(Event.id == decision.event_id).first()
        target_action = self.ACTION_REGISTRY.get(event.event_type, "RETRY")

        decision.chosen_action = target_action
        decision.status = "APPROVED"
        self.db.commit()

        # Execute
        result = self.executor.execute_action(decision.id, target_action, params)
        return {"status": "APPROVED_AND_EXECUTED", "action": target_action, "result": result}
