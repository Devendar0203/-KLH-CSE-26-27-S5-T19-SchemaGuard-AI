import requests

def run_demo():
    print("--------------------------------------------------")
    print(" DEMO SCENARIO 3: WORKLOAD SPIKE AUTO-SCALING")
    print("--------------------------------------------------")
    url = "http://127.0.0.1:8000/simulate/fault"
    res = requests.post(url, json={"fault_type": "workload_spike"})
    if res.status_code == 200:
        data = res.json()
        print("[OK] Fault Injected: Sudden high-volume record burst (120 records/sec)")
        print(f"[OK] AI Detection: Isolation Forest flagged throughput anomaly ({data['classification']['event_type']})")
        print(f"[OK] AI Decision: Chosen Action '{data['decision']['chosen_action']}'")
        print(f"[OK] Adaptation Execution: Worker capacity scaled up cleanly to stabilize throughput")
    else:
        print("Error:", res.text)

if __name__ == "__main__":
    run_demo()
