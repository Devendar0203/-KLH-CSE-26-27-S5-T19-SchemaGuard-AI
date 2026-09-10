import sys
import os
import time
import subprocess

def start_all():
    print("==================================================")
    print("   SCHEMAGUARD AI — SELF-HEALING PIPELINE DEMO   ")
    print("==================================================")

    base_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, base_dir)

    # 1. Initialize Database
    print("[1/3] Initializing Database Schema...")
    from backend.app.database import engine, Base
    Base.metadata.create_all(bind=engine)

    # 2. Launch Backend FastAPI
    print("[2/3] Launching FastAPI Backend Server (http://127.0.0.1:8000)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=base_dir
    )

    # 3. Launch Frontend Vite App
    frontend_dir = os.path.join(base_dir, "frontend")
    print("[3/3] Launching React Dashboard (http://localhost:5173)...")
    frontend_proc = subprocess.Popen(
        ["npx", "vite", "--port", "5173"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n--------------------------------------------------")
    print("✓ SchemaGuard AI System Operational!")
    print("  - Backend API:       http://127.0.0.1:8000")
    print("  - API Interactive:   http://127.0.0.1:8000/docs")
    print("  - Live React UI:     http://localhost:5173")
    print("  - Fault Demos:       python scripts/fault_injection/01_schema_drift.py")
    print("--------------------------------------------------")
    print("Press Ctrl+C to terminate services.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    start_all()
