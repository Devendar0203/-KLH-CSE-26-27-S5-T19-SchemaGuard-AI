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

def test_phase4():
    print("==================================================")
    print(" PHASE 4 VERIFICATION: VALIDATION, KNOWLEDGE & API")
    print("==================================================")

    # 1. Start FastAPI backend
    print("[1/4] Starting FastAPI backend server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if not wait_for_server("http://127.0.0.1:8000"):
        out, err = server.communicate()
        print("Server output:", out.decode())
        print("Server error:", err.decode())
        raise RuntimeError("FastAPI server failed to start within timeout.")

    try:
        # 2. Test Live Snapshot Endpoint
        print("[2/4] Testing GET /live endpoint...")
        res_live = requests.get("http://127.0.0.1:8000/live")
        assert res_live.status_code == 200, f"GET /live returned status {res_live.status_code}"
        live_json = res_live.json()
        print(" Live Snapshot status summary:", live_json["status_summary"])

        # 3. Test Fault Simulation for all 5 types
        print("[3/4] Testing POST /simulate/fault for all fault types...")
        faults = ["schema_drift", "bad_data", "worker_crash", "db_outage", "workload_spike"]
        for f in faults:
            r = requests.post("http://127.0.0.1:8000/simulate/fault", json={"fault_type": f})
            assert r.status_code == 200, f"Simulation {f} failed with status {r.status_code}"
            sim_res = r.json()
            dec = sim_res["decision"]
            print(f"  Fault '{f}' -> Event: '{sim_res['classification']['event_type']}', Chosen Action: '{dec['chosen_action']}', Status: '{dec['status']}'")

        # 4. Test Knowledge Base History & Human Approval
        print("[4/4] Testing GET /knowledge-base/history & Human Approval Endpoint...")
        res_kb = requests.get("http://127.0.0.1:8000/knowledge-base/history")
        assert res_kb.status_code == 200
        kb_list = res_kb.json()
        print(f" Knowledge Base Logged Entries ({len(kb_list)}):")
        for k in kb_list[:5]:
            print(f"   Event: {k['event_type']} -> Action: {k['action']} | Outcome: {k['outcome']} | Success: {k['success_bool']}")

    finally:
        server.terminate()
        server.wait()

    print("\n==================================================")
    print("  PHASE 4 VERIFICATION SUCCESSFUL!                ")
    print("==================================================")

if __name__ == "__main__":
    test_phase4()
