import requests
import json

URL = "http://localhost:8000/asp/v1/submit-validated"
params = {
    "source_module": "Verification Script",
    "source_filename": "verify.json"
}
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "demo-client-phase2"
}
data = ["INV-2026-AE-001"]

try:
    response = requests.post(URL, params=params, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
