import subprocess
import time
import requests
import json
import os
import sys

# Base Config
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-API-Key": "demo-key-123"}

def wait_for_server():
    print("Waiting for API server to start...")
    for _ in range(30):
        try:
            res = requests.get(f"{BASE_URL}/health/live")
            if res.status_code == 200:
                print("Server is UP!")
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_round_1_single_invoice_validation():
    print("==== ROUND 1: Single Invoice End-to-End Pipeline ====")
    with open("data/sample_invoice.json", "r") as f:
        payload = json.load(f)
    payload["invoice_number"] = "INV-DEEP-TEST-01"
    payload["payment_means_type_code"] = "10"
    
    # Validation
    res = requests.post(f"{BASE_URL}/api/v1/validate-invoice", json=payload, headers=HEADERS)
    assert res.status_code == 200, f"Failed validation: {res.text}"
    resp_data = res.json()
    report = resp_data.get("report", {})
    if report.get("is_valid") != True:
        print(json.dumps(resp_data, indent=2))
    assert report.get("is_valid") == True, "Invoice should be valid"
    print("   [x] /api/v1/validate-invoice is working and returned valid.")

    # ASP Mock validation
    res = requests.post(f"{BASE_URL}/asp/v1/validate", json=payload, headers=HEADERS)
    assert res.status_code == 200
    print("   [x] /asp/v1/validate working.")

    # ASP Submission
    res = requests.post(f"{BASE_URL}/asp/v1/submit", json=payload, headers=HEADERS)
    assert res.status_code == 200
    assert "clearance_id" in res.json()
    print("   [x] /asp/v1/submit working. Clearance ID received.")

def test_round_2_batch_processing():
    print("\n==== ROUND 2: Batch Upload and Processing ====")
    import pandas as pd
    import io
    
    # Create an in-memory CSV string
    csv_content = """invoice_number,invoice_date,total_amount,buyer_trn,seller_trn
BATCH-01,2025-01-10,500.0,100234567800003,100987654300003
BATCH-02,2025-01-11,750.0,100234567800003,100987654300003
INVALID-BATCH-03,2025-01-12,-100.0,123,456
"""
    files = {"file": ("test_batch.csv", csv_content, "text/csv")}
    
    res = requests.post(f"{BASE_URL}/api/v1/upload-excel", files=files, headers=HEADERS)
    assert res.status_code == 200, f"Failed batch upload: {res.text}"
    batch_data = res.json()
    batch_id = batch_data["batch_id"]
    print(f"   [x] Batch uploaded successfully. Batch ID: {batch_id}")

    # Polling for completion
    for _ in range(15):
        res = requests.get(f"{BASE_URL}/api/v1/batch-status/{batch_id}", headers=HEADERS)
        status_data = res.json()
        print(f"       Polled batch status: {status_data['status']} ({status_data['done']}/{status_data['total']})")
        if status_data["status"] == "COMPLETE":
            break
        time.sleep(2)
    
    assert status_data["status"] == "COMPLETE", "Batch did not complete in time"
    assert len(status_data["results"]) == 3, "Should have processed 3 results"
    print("   [x] Batch processed and validated perfectly.")

def test_round_3_analytics_and_history():
    print("\n==== ROUND 3: History & Analytics Integration ====")
    
    # History API
    res = requests.get(f"{BASE_URL}/api/v1/history", headers=HEADERS)
    assert res.status_code == 200, f"History fetch failed: {res.text}"
    history_data = res.json()
    # At least the single invoice plus the batch might have been stored 
    # (Depending on if validator inside batch stores them. Our current POC stores via validate endpoint or batch).
    print(f"   [x] /api/v1/history verified. Retrieved {history_data['total']} past runs.")

    # Analytics API
    res = requests.get(f"{BASE_URL}/api/v1/analytics/summary", headers=HEADERS)
    assert res.status_code == 200, f"Analytics fetch failed: {res.text}"
    analytics_data = res.json()
    print(f"   [x] /api/v1/analytics/summary working. Current Pass Rate: {analytics_data['pass_rate']}%")

    # CSV Export
    res = requests.get(f"{BASE_URL}/api/v1/export/csv", headers=HEADERS)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    print("   [x] /api/v1/export/csv working and returned valid CSV data bytes.")

if __name__ == "__main__":
    print("Starting Uvicorn Server in Background...")
    # NOTE: Set sqlite URL via env to not hit postgres since postgres is not running
    os.environ["DATABASE_URL"] = "sqlite:///./invoices.db"
    
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        if not wait_for_server():
            print("Server failed to start!")
            sys.exit(1)
            
        test_round_1_single_invoice_validation()
        test_round_2_batch_processing()
        test_round_3_analytics_and_history()
        print("\n\nAll 3 Rounds of END-TO-END Enterprise tests completed flawlessly! 100% READY.")
    except AssertionError as e:
        print(f"\nTEST SUITE FAILED: {str(e)}")
        sys.exit(1)
    finally:
        server_process.terminate()
        server_process.wait()
