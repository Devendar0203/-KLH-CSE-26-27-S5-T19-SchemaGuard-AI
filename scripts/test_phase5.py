import sys
import os
import time
import subprocess
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def wait_for_server(url: str, timeout: int = 15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/pipeline/status")
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_phase5_demos():
    print("==================================================")
    print("  PHASE 5 HARDENING: ALL 4 DEMO SCENARIOS TEST    ")
    print("==================================================")

    # 1. Start FastAPI backend
    print("Starting FastAPI Backend Server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )

    if not wait_for_server("http://127.0.0.1:8000"):
        server.terminate()
        raise RuntimeError("FastAPI server failed to start.")

    try:
        demos = [
            ("01_schema_drift.py", "scripts/fault_injection/01_schema_drift.py"),
            ("02_worker_failure.py", "scripts/fault_injection/02_worker_failure.py"),
            ("03_workload_spike.py", "scripts/fault_injection/03_workload_spike.py"),
            ("04_db_failure.py", "scripts/fault_injection/04_db_failure.py")
        ]

        for name, script_path in demos:
            print(f"\n---> Executing Demo Script: {name}")
            p = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
            print(p.stdout)
            if p.returncode != 0:
                print("Error output:", p.stderr)
            assert p.returncode == 0, f"Demo script {name} failed!"

    finally:
        server.terminate()
        server.wait()

    print("==================================================")
    print("  ALL 4 DEMO SCENARIOS PASSED AUTOMATICALLY!      ")
    print("==================================================")

if __name__ == "__main__":
    test_phase5_demos()
