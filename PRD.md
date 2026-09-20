# Product Requirements Document (PRD)
## SchemaGuard AI — Self-Adaptive, Self-Healing Data Pipeline

---

## 1. Document Control & Metadata

| Field | Details |
|---|---|
| **Product Name** | SchemaGuard AI |
| **Architectural Model** | MAPE-K Framework (Monitor, Analyze, Plan, Execute, Knowledge) |
| **Target Release** | v1.0.0 (Production Demo Ready) |
| **Status** | Approved & Implemented |
| **Repository** | [Devendar0203/-KLH-CSE-26-27-S5-T19-SchemaGuard-AI](https://github.com/Devendar0203/-KLH-CSE-26-27-S5-T19-SchemaGuard-AI) |

---

## 2. Product Overview & Executive Summary

### 2.1 Problem Statement
Modern data engineering pipelines suffer from high operational overhead due to frequent runtime anomalies—including unexpected schema drift (column renames/omissions), malformed input data, worker process crashes, transient database outages, and unannounced traffic spikes. Traditional orchestration platforms require manual engineer intervention to debug stack traces, write ad-hoc migration fixes, restart worker nodes, or quarantine corrupt records, causing prolonged pipeline downtimes and degraded data freshness.

### 2.2 Product Vision
**SchemaGuard AI** provides an autonomous, self-healing data pipeline orchestration layer. Utilizing the **MAPE-K architectural model**, the system continuously monitors data ingestion runtime signals, leverages machine learning models to detect anomalies and semantic schema variations, evaluates deterministic recovery actions from a closed safe action registry, executes automated adaptations, validates post-recovery system state, and logs lessons learned into a persistent Knowledge Base. A live React dashboard surfaces real-time system state, decision rationales, and human-in-the-loop approval workflows.

---

## 3. System Architecture & Tech Stack

### 3.1 Architectural Flow (MAPE-K Loop)

```
       +-----------------------------------------------------------+
       |                  DATA INGESTION PIPELINE                  |
       +-----------------------------------------------------------+
                                     |
                                  [Ingest]
                                     v
                       +---------------------------+
                       |    MONITOR (M) PROBES     |
                       | Schema, Heartbeat, Rate   |
                       +---------------------------+
                                     |
                             [Runtime Metrics]
                                     v
                       +---------------------------+
                       |    ANALYZE (A) AI LAYER   |
                       | Isolation Forest, ST-Sim  |
                       +---------------------------+
                                     |
                              [Classified Event]
                                     v
                       +---------------------------+
                       |    PLAN (P) DECISION      |
                       | Action Registry Mapping   |
                       +---------------------------+
                                     |
                         [Safe Approved Action]
                                     v
                       +---------------------------+
                       |    EXECUTE (E) ENGINES    |
                       | Adaptation Executors      |
                       +---------------------------+
                                     |
                         [Validate & Learn]
                                     v
                       +---------------------------+
                       |   KNOWLEDGE BASE (K)      |
                       | Self-Learning Logs & UI   |
                       +---------------------------+
```

### 3.2 Technology Stack

| Layer | Component | Choice / Specification |
|---|---|---|
| **Backend API** | REST API Framework | FastAPI (Python 3.11+) |
| **Orchestration** | Pipeline DAG Orchestrator | Apache Airflow / Airflow-compatible DAG Runtime |
| **Database & ORM** | Relational Storage & Data Models | PostgreSQL / SQLite with SQLAlchemy 2.0 |
| **AI / ML Models** | Anomaly Detection | `scikit-learn` (`IsolationForest`) |
| **AI / ML Models** | Semantic Field Matching | `sentence-transformers` (`all-MiniLM-L6-v2`) + Cosine Similarity |
| **Frontend UI** | Live Dashboard | React 18, Vite 5, Tailwind CSS |
| **Containerization** | Infrastructure Orchestration | Docker & Docker Compose |

---

## 4. Functional Requirements (FRs)

### FR-1: Core Ingestion Engine
- **FR-1.1**: Accept record batches via REST endpoint (`POST /ingest`).
- **FR-1.2**: Execute scheduled Airflow DAGs (`pipeline/dags/ingest_dag.py`) ingesting multi-format data sources (CSV files, Mock JSON APIs).
- **FR-1.3**: Dynamically apply stored active schema mappings before record validation.
- **FR-1.4**: Validate records against required fields (`customer_id`, `first_name`, `last_name`) and numeric formats (`account_balance`). Write valid records to `customers` table; route invalid records to `quarantine` table.

### FR-2: Real-time Health Probes & Monitoring Engine
- **FR-2.1**: Collect schema fingerprints comparing incoming batch keys against stored historical `schema_versions`.
- **FR-2.2**: Maintain worker heartbeat registry (`worker_health`) tracking node status, last heartbeat timestamp, and restart counts. Mark nodes dead if heartbeat > 15 seconds old.
- **FR-2.3**: Aggregate metric windows including batch record throughput, processing latency (ms), quarantine rate, and database connection status.

### FR-3: AI Detection & Analysis Layer
- **FR-3.1 Anomaly Detection**: `ai_engine/anomaly_detector.py` runs `IsolationForest` on rolling metric vectors `[record_count, error_rate, latency_ms, quarantine_rate]` to output anomaly index ($0.0 - 1.0$) and classification.
- **FR-3.2 Semantic Schema Matching**: `ai_engine/schema_matcher.py` uses `sentence-transformers` (`all-MiniLM-L6-v2`) embeddings + cosine similarity to identify field renames (e.g., matching `customerId` to `customer_id` above $0.70$ confidence threshold).
- **FR-3.3 Failure Classification**: `ai_engine/failure_classifier.py` evaluates evidence to categorize problems into canonical event types:
  1. `schema_drift` (unexpected/missing fields with semantic match)
  2. `bad_data` (high quarantine count / numeric type errors)
  3. `worker_crash` (crashed worker status / expired heartbeat)
  4. `db_outage` (unreachable database connection)
  5. `workload_spike` (anomalous record throughput spike)

### FR-4: Safe AI Decision Engine & Action Registry
- **Hard Constraint**: AI must never generate or execute un-sanitized code, arbitrary SQL, or free-form shell scripts.
- **FR-4.1 Action Mapping**: Map classified events exclusively to approved fixed action registry:
  - `schema_drift` $\rightarrow$ `MAP_SCHEMA`
  - `bad_data` $\rightarrow$ `QUARANTINE_DATA`
  - `worker_crash` $\rightarrow$ `RESTART_WORKER`
  - `db_outage` $\rightarrow$ `BUFFER`
  - `workload_spike` $\rightarrow$ `SCALE_WORKERS`
- **FR-4.2 Confidence Thresholding**:
  - If decision confidence $\ge 0.80$: Mark status `EXECUTED` and trigger adaptation executor automatically.
  - If decision confidence $< 0.80$ or flagged as high risk: Set chosen action to `HUMAN_APPROVAL` and status to `PENDING_APPROVAL`.
- **FR-4.3 Human-in-the-Loop Override**: Provide manual approval endpoint (`POST /actions/{id}/approve`) to allow human operators to review and execute pending actions.

### FR-5: Adaptation Executors & Rollback Paths
- **FR-5.1 MAP_SCHEMA**: Persist new field alias mapping into `active_schema_mappings` table. Provide rollback routine (`rollback_map_schema`).
- **FR-5.2 QUARANTINE_DATA**: Isolate offending records into `quarantine` table with timestamp and error reason.
- **FR-5.3 RESTART_WORKER**: Re-initialize worker process state to `HEALTHY` and increment `restart_count`.
- **FR-5.4 BUFFER**: Divert incoming records to persistent buffer queue (`buffered_records.json`) during DB outage, with auto-flush on DB restoration.
- **FR-5.5 SCALE_WORKERS**: Dynamically adjust active worker node allocation from $N$ to $N+k$.

### FR-6: Post-Adaptation Validation & Knowledge Base
- **FR-6.1 Validation Check**: Execute post-adaptation health probe to confirm pipeline recovery (e.g., verifying worker status or active schema mapping).
- **FR-6.2 Knowledge Logging**: Write outcome tuple `(event_type, action, outcome, success_bool, created_at)` into `knowledge_base` table to build a queryable historical memory.

### FR-7: Live Dashboard & Demo Controls
- **FR-7.1 Live Polling**: Poll `GET /live` every 2 seconds to render real-time pipeline status, active worker nodes, event feed, decision log, and knowledge history.
- **FR-7.2 Fault Simulation Panel**: Provide 1-click trigger controls for all 5 fault scenarios (`POST /simulate/fault`).
- **FR-7.3 Decision UI**: Display confidence progress bar, plain-language rationale, and interactive **Approve & Execute** buttons for pending human approvals.

---

## 5. Non-Functional Requirements (NFRs)

| Category | Metric / Specification |
|---|---|
| **Latency** | Anomaly detection and action selection completed in $< 500\text{ ms}$. Total self-healing recovery completed in $< 2.0\text{ s}$. |
| **Availability** | Pipeline stays operational or degrades gracefully (buffering records) during database outages. |
| **Safety** | Zero free-form code execution. AI decisions restricted 100% to the pre-approved action registry. |
| **Portability** | Multi-platform support (Windows host native execution and Linux Docker/docker-compose deployment). |
| **Observability** | Complete audit trail maintained across `events`, `decisions`, `actions_log`, and `knowledge_base` tables. |

---

## 6. Data Model Specification

```sql
-- Pipeline Runs
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    dag_run_id VARCHAR(255) INDEX,
    source VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    status VARCHAR(50) -- RUNNING, SUCCESS, FAILED, HEALED
);

-- Schema Versions
CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) INDEX,
    field_name VARCHAR(100),
    field_type VARCHAR(50),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Detected Events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES pipeline_runs(id),
    event_type VARCHAR(100) INDEX, -- schema_drift, bad_data, worker_crash, db_outage, workload_spike
    severity VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evidence_json TEXT
);

-- AI Decisions
CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    chosen_action VARCHAR(100), -- MAP_SCHEMA, QUARANTINE_DATA, RESTART_WORKER, BUFFER, SCALE_WORKERS, HUMAN_APPROVAL
    confidence FLOAT,
    rationale TEXT,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'EXECUTED' -- EXECUTED, PENDING_APPROVAL, APPROVED
);

-- Execution Logs
CREATE TABLE actions_log (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER REFERENCES decisions(id),
    action VARCHAR(100),
    status VARCHAR(50), -- SUCCESS, FAILED, ROLLED_BACK
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_json TEXT
);

-- Quarantine Storage
CREATE TABLE quarantine (
    id SERIAL PRIMARY KEY,
    run_id INTEGER,
    record_json TEXT,
    reason TEXT,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Worker Health Status
CREATE TABLE worker_health (
    id SERIAL PRIMARY KEY,
    worker_name VARCHAR(100) UNIQUE INDEX,
    status VARCHAR(50), -- HEALTHY, CRASHED, BUSY
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restart_count INTEGER DEFAULT 0
);

-- Self-Learning Knowledge Base
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) INDEX,
    action VARCHAR(100),
    outcome TEXT,
    success_bool BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Target Data Table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) INDEX,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    signup_date VARCHAR(50),
    account_balance FLOAT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Active Self-Healed Schema Mappings
CREATE TABLE active_schema_mappings (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) INDEX,
    original_field VARCHAR(100),
    target_field VARCHAR(100),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. API Interface Specifications

### 7.1 `POST /ingest`
- **Description**: Accept data batch for ingestion.
- **Request Body**:
  ```json
  {
    "source_name": "customers_csv",
    "dag_run_id": "dag_csv_1001",
    "records": [
      {
        "customer_id": "CUST-1001",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "signup_date": "2026-01-15",
        "account_balance": 1250.50
      }
    ]
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "run_id": 1,
    "status": "SUCCESS",
    "processed_count": 1,
    "quarantined_count": 0,
    "events_triggered": []
  }
  ```

### 7.2 `GET /live`
- **Description**: Consolidated real-time snapshot for the React dashboard.
- **Response** (`200 OK`): Returns `status_summary`, `workers`, `events`, `decisions`, `knowledge_base`, and `actions_log`.

### 7.3 `POST /simulate/fault`
- **Description**: Trigger a fault simulation scenario.
- **Request Body**:
  ```json
  {
    "fault_type": "schema_drift",
    "source_name": "customers_csv"
  }
  ```
- **Supported `fault_type` values**: `schema_drift`, `bad_data`, `worker_crash`, `db_outage`, `workload_spike`.

### 7.4 `POST /actions/{id}/approve`
- **Description**: Execute human approval override for pending decisions.
- **Response** (`200 OK`): `{"status": "APPROVED_AND_EXECUTED", "action": "SCALE_WORKERS", "result": {...}}`

---

## 8. Acceptance Criteria & Demo Verification

| Scenario | Trigger Condition | Expected AI Action | Success Acceptance Criteria |
|---|---|---|---|
| **1. Schema Drift** | Header modified (`customer_id` $\rightarrow$ `customerId`) | `MAP_SCHEMA` | Semantic similarity $> 0.90$. Field mapping saved to `active_schema_mappings`. Subsequent ingestion succeeds automatically. |
| **2. Worker Failure** | Worker process killed / heartbeat expired | `RESTART_WORKER` | Heartbeat probe detects failure within $2\text{ s}$. Worker state reset to `HEALTHY` and restart count incremented. |
| **3. Workload Spike** | High-volume batch burst (120 records/sec) | `SCALE_WORKERS` | `IsolationForest` flags throughput anomaly. Worker node pool scaled from $1$ to $N+k$. |
| **4. DB Outage** | Database connection timeout | `BUFFER` | Ingestion layer captures incoming records into persistent buffer queue without dropping data. |
| **5. Low Confidence** | Classification confidence $< 0.80$ | `HUMAN_APPROVAL` | Action routed to `HUMAN_APPROVAL`. Dashboard surfaces **Approve & Execute** button. Executed upon click. |

---

## 9. Project Directory Layout

```
schemaguard-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI application entry & router registration
│   │   ├── config.py              # Application configurations
│   │   ├── database.py            # SQLAlchemy engine & session setup
│   │   ├── models.py              # Database models (MAPE-K schema)
│   │   ├── schemas.py             # Pydantic API request/response schemas
│   │   ├── routers/               # Endpoint routers (ingest, status, events, decisions, etc.)
│   │   └── services/              # Ingestion & Knowledge Base business logic
├── pipeline/
│   ├── dags/
│   │   └── ingest_dag.py          # Airflow ingestion DAG definition
│   └── runner.py                  # Standalone pipeline executor
├── ai_engine/
│   ├── anomaly_detector.py        # Isolation Forest metric anomaly detector
│   ├── schema_matcher.py          # Sentence Transformers semantic similarity matcher
│   ├── failure_classifier.py      # Rule & metric failure classifier
│   └── decision_engine.py         # Safe AI decision engine & approval router
├── monitoring/
│   └── health_monitor.py          # Worker heartbeat & schema fingerprint probes
├── adaptation/
│   ├── map_schema.py              # MAP_SCHEMA adaptation executor
│   ├── quarantine_data.py         # QUARANTINE_DATA adaptation executor
│   ├── restart_worker.py          # RESTART_WORKER adaptation executor
│   ├── buffer_failover.py         # BUFFER adaptation executor
│   ├── scale_workers.py           # SCALE_WORKERS adaptation executor
│   └── executor.py                # Central ActionExecutor dispatcher
├── frontend/                      # React 18 + Vite live monitoring dashboard
├── data/                          # Sample CSV datasets & API mock fixtures
├── scripts/
│   └── fault_injection/          # Automated demo fault scripts (01-04)
├── docker-compose.yml             # Docker container orchestration
├── Dockerfile.backend             # Backend container definition
├── Dockerfile.frontend            # Frontend container definition
├── start_demo.py                  # Single-command launcher script
└── PRD.md                         # Product Requirements Document
```
