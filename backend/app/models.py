from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from datetime import datetime, timezone
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    dag_run_id = Column(String, index=True)
    source = Column(String)
    started_at = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="RUNNING") # RUNNING, SUCCESS, FAILED, HEALED

class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, index=True)
    field_name = Column(String)
    field_type = Column(String)
    first_seen = Column(DateTime, default=utc_now)
    last_seen = Column(DateTime, default=utc_now)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=True)
    event_type = Column(String, index=True) # schema_drift, bad_data, worker_crash, db_outage, workload_spike
    severity = Column(String) # LOW, MEDIUM, HIGH, CRITICAL
    detected_at = Column(DateTime, default=utc_now)
    evidence_json = Column(Text) # JSON string of detected details

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    chosen_action = Column(String) # MAP_SCHEMA, QUARANTINE_DATA, RESTART_WORKER, RETRY, BUFFER, FAILOVER, SCALE_WORKERS, HUMAN_APPROVAL, ROLLBACK
    confidence = Column(Float)
    rationale = Column(Text)
    decided_at = Column(DateTime, default=utc_now)
    status = Column(String, default="EXECUTED") # EXECUTED, PENDING_APPROVAL, APPROVED, REJECTED

class ActionLog(Base):
    __tablename__ = "actions_log"
    
    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"))
    action = Column(String)
    status = Column(String) # SUCCESS, FAILED, ROLLED_BACK
    executed_at = Column(DateTime, default=utc_now)
    result_json = Column(Text)

class Quarantine(Base):
    __tablename__ = "quarantine"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, nullable=True)
    record_json = Column(Text)
    reason = Column(Text)
    quarantined_at = Column(DateTime, default=utc_now)

class WorkerHealth(Base):
    __tablename__ = "worker_health"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_name = Column(String, unique=True, index=True)
    status = Column(String) # HEALTHY, CRASHED, BUSY, RESTARTING
    last_heartbeat = Column(DateTime, default=utc_now)
    restart_count = Column(Integer, default=0)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    action = Column(String)
    outcome = Column(Text)
    success_bool = Column(Boolean)
    created_at = Column(DateTime, default=utc_now)

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    signup_date = Column(String)
    account_balance = Column(Float)
    ingested_at = Column(DateTime, default=utc_now)

class ActiveSchemaMapping(Base):
    __tablename__ = "active_schema_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, index=True)
    original_field = Column(String) # e.g. customerId
    target_field = Column(String)   # e.g. customer_id
    confidence = Column(Float)
    created_at = Column(DateTime, default=utc_now)
