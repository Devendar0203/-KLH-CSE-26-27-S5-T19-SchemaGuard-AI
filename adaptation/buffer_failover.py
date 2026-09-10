import json
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import ActionLog

BUFFER_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "buffered_records.json")

def execute_buffer_records(db: Session, decision_id: int, records: list) -> dict:
    buffered = []
    if os.path.exists(BUFFER_FILE):
        try:
            with open(BUFFER_FILE, "r") as f:
                buffered = json.load(f)
        except Exception:
            buffered = []
            
    buffered.extend(records)
    with open(BUFFER_FILE, "w") as f:
        json.dump(buffered, f, indent=2)

    result_json = json.dumps({
        "status": "SUCCESS",
        "action": "BUFFER",
        "buffered_count": len(records),
        "total_buffer_depth": len(buffered)
    })

    log = ActionLog(
        decision_id=decision_id,
        action="BUFFER",
        status="SUCCESS",
        result_json=result_json,
        executed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    return {"status": "SUCCESS", "message": f"Buffered {len(records)} records safely (total buffer: {len(buffered)})"}

def flush_buffer(db: Session) -> list:
    if not os.path.exists(BUFFER_FILE):
        return []
    with open(BUFFER_FILE, "r") as f:
        records = json.load(f)
    os.remove(BUFFER_FILE)
    return records
