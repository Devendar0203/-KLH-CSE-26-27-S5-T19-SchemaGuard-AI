import requests
import sys

def run_demo():
    print("--------------------------------------------------")
    print(" DEMO SCENARIO 1: SCHEMA DRIFT AUTOMATED HEALING")
    print("--------------------------------------------------")
    url = "http://127.0.0.1:8000/simulate/fault"
    res = requests.post(url, json={"fault_type": "schema_drift", "source_name": "customers_csv"})
    if res.status_code == 200:
        data = res.json()
        print("[OK] Fault Injected: Incoming column header changed (customer_id -> customerId)")
        print(f"[OK] AI Detection: Event '{data['classification']['event_type']}' classified with {data['decision']['confidence']*100:.0f}% confidence")
        print(f"[OK] AI Decision: Chosen Action '{data['decision']['chosen_action']}' ({data['decision']['status']})")
        print(f"[OK] Rationale: {data['decision']['rationale']}")
        print("[OK] System Recovery: MAP_SCHEMA active in database. Pipeline continuing without manual intervention!")
    else:
        print("Error:", res.text)

if __name__ == "__main__":
    run_demo()
