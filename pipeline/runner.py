import sys
import os
from pipeline.dags.ingest_dag import run_csv_ingestion, run_api_ingestion

def execute_pipeline(backend_url: str = "http://127.0.0.1:8000"):
    print("--- Starting SchemaGuard Pipeline DAG Run ---")
    res_csv = run_csv_ingestion(backend_url)
    res_api = run_api_ingestion(backend_url)
    print("--- DAG Run Completed Successfully ---")
    return {"csv": res_csv, "api": res_api}

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    execute_pipeline(url)
