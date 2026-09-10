import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Event

router = APIRouter(prefix="", tags=["Events"])

@router.get("/events")
def get_events(limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.id.desc()).limit(limit).all()
    res = []
    for e in events:
        evidence = json.loads(e.evidence_json) if e.evidence_json else {}
        res.append({
            "id": e.id,
            "run_id": e.run_id,
            "event_type": e.event_type,
            "severity": e.severity,
            "detected_at": e.detected_at.isoformat() if e.detected_at else None,
            "evidence": evidence
        })
    return res

@router.get("/events/{event_id}")
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    e = db.query(Event).filter(Event.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": e.id,
        "run_id": e.run_id,
        "event_type": e.event_type,
        "severity": e.severity,
        "detected_at": e.detected_at.isoformat() if e.detected_at else None,
        "evidence": json.loads(e.evidence_json) if e.evidence_json else {}
    }
