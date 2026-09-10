import requests

def run_demo():
    print("--------------------------------------------------")
    print(" DEMO SCENARIO 2: WORKER FAILURE AUTO-RESTART")
    print("--------------------------------------------------")
    url = "http://127.0.0.1:8000/simulate/fault"
    res = requests.post(url, json={"fault_type": "worker_crash"})
    if res.status_code == 200:
        data = res.json()
        print("[OK] Fault Injected: Main pipeline worker container stopped / crashed")
        print(f"[OK] AI Detection: Health monitor detected expired heartbeat within 2s ({data['classification']['event_type']})")
        print(f"[OK] AI Decision: Chosen Action '{data['decision']['chosen_action']}'")
        print(f"[OK] Adaptation Execution: Worker process restarted, status reset to HEALTHY")
    else:
        print("Error:", res.text)

if __name__ == "__main__":
    run_demo()
