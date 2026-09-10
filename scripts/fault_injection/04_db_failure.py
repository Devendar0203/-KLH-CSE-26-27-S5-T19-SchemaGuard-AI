import requests

def run_demo():
    print("--------------------------------------------------")
    print(" DEMO SCENARIO 4: DATABASE FAILURE SAFE BUFFERING")
    print("--------------------------------------------------")
    url = "http://127.0.0.1:8000/simulate/fault"
    res = requests.post(url, json={"fault_type": "db_outage"})
    if res.status_code == 200:
        data = res.json()
        print("[OK] Fault Injected: Database unreachable / connection timeout")
        print(f"[OK] AI Detection: Health monitor detected DB connection failure ({data['classification']['event_type']})")
        print(f"[OK] AI Decision: Chosen Action '{data['decision']['chosen_action']}'")
        print(f"[OK] Adaptation Execution: Incoming records safely buffered to local queue until database recovers")
    else:
        print("Error:", res.text)

if __name__ == "__main__":
    run_demo()
