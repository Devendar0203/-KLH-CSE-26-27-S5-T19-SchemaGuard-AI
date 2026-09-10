import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import Quarantine, ActionLog

def execute_quarantine_data(db: Session, decision_id: int, run_id: int, records: list, reason: str) -> dict:
    quarantined_count = 0
    for rec in records:
        q = Quarantine(
            run_id=run_id,
            record_json=json.dumps(rec) if not isinstance(rec, str) else rec,
            reason=reason,
            quarantined_at=datetime.now(timezone.utc)
        )
        db.add(q)
        quarantined_count += 1

    result_json = json.dumps({
        "status": "SUCCESS",
        "action": "QUARANTINE_DATA",
        "quarantined_count": quarantined_count,
        "reason": reason
    })

    log = ActionLog(
        decision_id=decision_id,
        action="QUARANTINE_DATA",
        status="SUCCESS",
        result_json=result_json,
        executed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    return {"status": "SUCCESS", "quarantined_count": quarantined_count}
