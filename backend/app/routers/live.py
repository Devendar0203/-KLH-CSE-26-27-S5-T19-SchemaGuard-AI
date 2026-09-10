import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import PipelineRun, Customer, Quarantine, WorkerHealth, Event, Decision, KnowledgeBase, ActionLog

router = APIRouter(prefix="", tags=["Live"])

@router.get("/live")
def get_live_snapshot(db: Session = Depends(get_db)):
    active_runs = db.query(PipelineRun).filter(PipelineRun.status == "RUNNING").count()
    total_runs = db.query(PipelineRun).count()
    total_records = db.query(Customer).count()
    total_quarantined = db.query(Quarantine).count()

    workers = db.query(WorkerHealth).all()
    worker_list = [{"name": w.worker_name, "status": w.status, "restart_count": w.restart_count, "last_heartbeat": w.last_heartbeat.isoformat() if w.last_heartbeat else None} for w in workers]

    events = db.query(Event).order_by(Event.id.desc()).limit(15).all()
    event_list = [{
        "id": e.id,
        "run_id": e.run_id,
        "event_type": e.event_type,
        "severity": e.severity,
        "detected_at": e.detected_at.isoformat() if e.detected_at else None,
        "evidence": json.loads(e.evidence_json) if e.evidence_json else {}
    } for e in events]

    decisions = db.query(Decision).order_by(Decision.id.desc()).limit(15).all()
    decision_list = [{
        "id": d.id,
        "event_id": d.event_id,
        "chosen_action": d.chosen_action,
        "confidence": d.confidence,
        "rationale": d.rationale,
        "status": d.status,
        "decided_at": d.decided_at.isoformat() if d.decided_at else None
    } for d in decisions]

    knowledge = db.query(KnowledgeBase).order_by(KnowledgeBase.id.desc()).limit(15).all()
    knowledge_list = [{
        "id": k.id,
        "event_type": k.event_type,
        "action": k.action,
        "outcome": k.outcome,
        "success_bool": k.success_bool,
        "created_at": k.created_at.isoformat() if k.created_at else None
    } for k in knowledge]

    actions = db.query(ActionLog).order_by(ActionLog.id.desc()).limit(15).all()
    action_list = [{
        "id": a.id,
        "decision_id": a.decision_id,
        "action": a.action,
        "status": a.status,
        "executed_at": a.executed_at.isoformat() if a.executed_at else None,
        "result": json.loads(a.result_json) if a.result_json else {}
    } for a in actions]

    return {
        "status_summary": {
            "active_runs": active_runs,
            "total_runs": total_runs,
            "total_records": total_records,
            "total_quarantined": total_quarantined,
            "system_health": "DEGRADED" if total_quarantined > 0 or any(w["status"] != "HEALTHY" for w in worker_list) else "HEALTHY"
        },
        "workers": worker_list,
        "events": event_list,
        "decisions": decision_list,
        "knowledge_base": knowledge_list,
        "actions_log": action_list
    }
