import sys
import os
import time
import subprocess
import requests

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, SessionLocal, Base
from backend.app.models import PipelineRun, Customer, SchemaVersion

def test_phase1():
    print("==================================================")
    print("  PHASE 1 VERIFICATION: CORE PIPELINE INGESTION   ")
    print("==================================================")
    
    # 1. Init DB tables
    print("[1/4] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Start FastAPI server in background or test process
    print("[2/4] Launching FastAPI Backend Server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to boot up
    time.sleep(3)
    try:
        r = requests.get("http://127.0.0.1:8000/pipeline/status")
        print(f"Backend Health Status Check: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"Server start failed: {e}")
        server_process.kill()
        sys.exit(1)
        
    # 3. Run Pipeline Ingestion DAG
    print("[3/4] Executing Ingestion DAG (CSV + API Mock sources)...")
    from pipeline.runner import execute_pipeline
    dag_results = execute_pipeline("http://127.0.0.1:8000")
    print("DAG Execution Result Summary:", dag_results)
    
    # 4. Query DB & Verify Rows landed
    print("[4/4] Querying Database Tables to Prove Data Landing...")
    db = SessionLocal()
    
    runs = db.query(PipelineRun).all()
    customers = db.query(Customer).all()
    schemas = db.query(SchemaVersion).all()
    
    print(f"\n--- PIPELINE RUNS ({len(runs)}) ---")
    for r in runs:
        print(f" Run ID: {r.id} | DAG Run ID: {r.dag_run_id} | Source: {r.source} | Status: {r.status}")
        
    print(f"\n--- INGESTED CUSTOMERS ({len(customers)}) ---")
    for c in customers:
        print(f" ID: {c.customer_id} | Name: {c.first_name} {c.last_name} | Email: {c.email} | Balance: ${c.account_balance:.2f}")
        
    print(f"\n--- REGISTERED SCHEMA VERSIONS ({len(schemas)}) ---")
    for s in schemas:
        print(f" Source: {s.source_name} | Field: {s.field_name} ({s.field_type})")
        
    db.close()
    
    # Terminate server process
    server_process.terminate()
    server_process.wait()
    
    print("\n==================================================")
    print("  PHASE 1 VERIFICATION SUCCESSFUL!                ")
    print("==================================================")

if __name__ == "__main__":
    test_phase1()
