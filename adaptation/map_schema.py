import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import ActiveSchemaMapping, ActionLog

def execute_map_schema(db: Session, decision_id: int, source_name: str, original_field: str, target_field: str, confidence: float) -> dict:
    # Check if mapping already exists
    existing = db.query(ActiveSchemaMapping).filter(
        ActiveSchemaMapping.source_name == source_name,
        ActiveSchemaMapping.original_field == original_field
    ).first()

    if not existing:
        new_map = ActiveSchemaMapping(
            source_name=source_name,
            original_field=original_field,
            target_field=target_field,
            confidence=confidence,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_map)
    else:
        existing.target_field = target_field
        existing.confidence = confidence

    result_json = json.dumps({
        "status": "SUCCESS",
        "action": "MAP_SCHEMA",
        "source": source_name,
        "mapping": f"{original_field} -> {target_field}",
        "confidence": confidence
    })

    log = ActionLog(
        decision_id=decision_id,
        action="MAP_SCHEMA",
        status="SUCCESS",
        result_json=result_json,
        executed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    return {"status": "SUCCESS", "message": f"Successfully mapped '{original_field}' to '{target_field}' for {source_name}"}

def rollback_map_schema(db: Session, source_name: str, original_field: str) -> dict:
    db.query(ActiveSchemaMapping).filter(
        ActiveSchemaMapping.source_name == source_name,
        ActiveSchemaMapping.original_field == original_field
    ).delete()
    db.commit()
    return {"status": "ROLLED_BACK", "message": f"Removed schema mapping for '{original_field}'"}
