from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import KnowledgeBase

router = APIRouter(prefix="", tags=["KnowledgeBase"])

@router.get("/knowledge-base/history")
def get_knowledge_history(limit: int = 50, db: Session = Depends(get_db)):
    history = db.query(KnowledgeBase).order_by(KnowledgeBase.id.desc()).limit(limit).all()
    res = []
    for k in history:
        res.append({
            "id": k.id,
            "event_type": k.event_type,
            "action": k.action,
            "outcome": k.outcome,
            "success_bool": k.success_bool,
            "created_at": k.created_at.isoformat() if k.created_at else None
        })
    return res
