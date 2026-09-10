from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Decision
from ai_engine.decision_engine import DecisionEngine

router = APIRouter(prefix="", tags=["Decisions"])

@router.get("/decisions")
def get_decisions(limit: int = 50, db: Session = Depends(get_db)):
    decisions = db.query(Decision).order_by(Decision.id.desc()).limit(limit).all()
    res = []
    for d in decisions:
        res.append({
            "id": d.id,
            "event_id": d.event_id,
            "chosen_action": d.chosen_action,
            "confidence": d.confidence,
            "rationale": d.rationale,
            "status": d.status,
            "decided_at": d.decided_at.isoformat() if d.decided_at else None
        })
    return res

@router.post("/actions/{decision_id}/approve")
def approve_action(decision_id: int, db: Session = Depends(get_db)):
    engine_inst = DecisionEngine(db)
    try:
        result = engine_inst.approve_human_decision(decision_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
