import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models import PipelineRun, Customer, Quarantine, SchemaVersion, ActiveSchemaMapping

def process_ingest_batch(db: Session, source_name: str, dag_run_id: str, records: list) -> dict:
    run = PipelineRun(
        dag_run_id=dag_run_id,
        source=source_name,
        started_at=datetime.now(timezone.utc),
        status="RUNNING"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Retrieve active schema mappings for this source
    active_mappings = db.query(ActiveSchemaMapping).filter(ActiveSchemaMapping.source_name == source_name).all()
    field_map = {m.original_field: m.target_field for m in active_mappings}

    processed_count = 0
    quarantined_count = 0

    for rec in records:
        # Apply schema mapping if present
        mapped_rec = {}
        for k, v in rec.items():
            target_key = field_map.get(k, k)
            mapped_rec[target_key] = v

        # Basic record validation
        # Check required fields
        required_fields = ["customer_id", "first_name", "last_name"]
        missing_fields = [rf for rf in required_fields if rf not in mapped_rec or mapped_rec[rf] is None]

        if missing_fields:
            # Quarantine invalid record
            q = Quarantine(
                run_id=run.id,
                record_json=json.dumps(rec),
                reason=f"Missing required fields: {', '.join(missing_fields)}"
            )
            db.add(q)
            quarantined_count += 1
            continue

        # Check numerical sanity (e.g., account balance type)
        balance = mapped_rec.get("account_balance", 0.0)
        try:
            balance = float(balance) if balance is not None else 0.0
        except (ValueError, TypeError):
            q = Quarantine(
                run_id=run.id,
                record_json=json.dumps(rec),
                reason=f"Invalid account_balance numeric format: {balance}"
            )
            db.add(q)
            quarantined_count += 1
            continue

        # Record schema version fields
        for field_name, val in mapped_rec.items():
            field_type = type(val).__name__
            existing_sv = db.query(SchemaVersion).filter(
                SchemaVersion.source_name == source_name,
                SchemaVersion.field_name == field_name
            ).first()
            if not existing_sv:
                db.add(SchemaVersion(
                    source_name=source_name,
                    field_name=field_name,
                    field_type=field_type,
                    first_seen=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc)
                ))
            else:
                existing_sv.last_seen = datetime.now(timezone.utc)

        # Save valid customer record
        c = Customer(
            customer_id=str(mapped_rec.get("customer_id")),
            first_name=str(mapped_rec.get("first_name", "")),
            last_name=str(mapped_rec.get("last_name", "")),
            email=str(mapped_rec.get("email", "")),
            signup_date=str(mapped_rec.get("signup_date", "")),
            account_balance=balance
        )
        db.add(c)
        processed_count += 1

    run.ended_at = datetime.now(timezone.utc)
    run.status = "SUCCESS" if quarantined_count == 0 else ("HEALED" if processed_count > 0 else "FAILED")
    db.commit()

    return {
        "run_id": run.id,
        "status": run.status,
        "processed_count": processed_count,
        "quarantined_count": quarantined_count
    }
