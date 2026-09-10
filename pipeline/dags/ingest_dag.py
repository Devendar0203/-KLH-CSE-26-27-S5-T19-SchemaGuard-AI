import os
import json
import csv
import requests
from datetime import datetime, timedelta

def load_csv_data(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    records = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "account_balance" in row:
                try:
                    row["account_balance"] = float(row["account_balance"])
                except ValueError:
                    pass
            records.append(row)
    return records

def load_json_data(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, mode="r", encoding="utf-8") as f:
        return json.load(f)

def run_csv_ingestion(backend_url: str = "http://127.0.0.1:8000"):
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "customers_sample.csv")
    records = load_csv_data(csv_path)
    payload = {
        "source_name": "customers_csv",
        "dag_run_id": f"dag_csv_{int(datetime.now().timestamp())}",
        "records": records
    }
    response = requests.post(f"{backend_url}/ingest", json=payload)
    response.raise_for_status()
    print("CSV Ingestion Result:", response.json())
    return response.json()

def run_api_ingestion(backend_url: str = "http://127.0.0.1:8000"):
    json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "api_mock.json")
    records = load_json_data(json_path)
    payload = {
        "source_name": "api_mock",
        "dag_run_id": f"dag_api_{int(datetime.now().timestamp())}",
        "records": records
    }
    response = requests.post(f"{backend_url}/ingest", json=payload)
    response.raise_for_status()
    print("API Mock Ingestion Result:", response.json())
    return response.json()

# Standard Airflow DAG definition pattern (runs in Apache Airflow if present)
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

    default_args = {
        'owner': 'schemaguard',
        'depends_on_past': False,
        'start_date': datetime(2026, 1, 1),
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    }

    dag = DAG(
        'schemaguard_ingest_dag',
        default_args=default_args,
        description='Ingest customer CSV and API mock sources into SchemaGuard DB',
        schedule_interval=timedelta(hours=1),
        catchup=False,
    )

    t1 = PythonOperator(
        task_id='ingest_csv_source',
        python_callable=run_csv_ingestion,
        dag=dag,
    )

    t2 = PythonOperator(
        task_id='ingest_api_source',
        python_callable=run_api_ingestion,
        dag=dag,
    )

    t1 >> t2
except ImportError:
    # Airflow not installed in local environment, fallback execution handled via pipeline/runner.py
    pass
