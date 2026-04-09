import requests
import json

def test_validation_failure_report():
    url = "http://localhost:8000/api/v1/validate-invoice"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "demo-key-123"
    }
    
    # Payload with missing required field 'invoice_date'
    payload = {
        "invoice_number": "FAIL-TEST-001",
        "transaction_type": "B2B",
        "seller": {
            "name": "Test Seller",
            "trn": "12345"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    data = response.json()
    print(f"API Status: {data.get('status')}")
    print(f"Message: {data.get('message')}")
    
    report = data.get("report", {})
    print(f"Is Valid (Report): {report.get('is_valid')}")
    print(f"Total Errors: {report.get('total_errors')}")
    
    field_results = report.get("field_results", [])
    if field_results:
        print("\nField Results Breakdown:")
        for group in field_results:
            print(f"Group: {group.get('group')}")
            for field in group.get("fields", []):
                print(f"  [{field.get('status')}] {field.get('label')}: {field.get('error')}")

if __name__ == "__main__":
    try:
        test_validation_failure_report()
    except Exception as e:
        print(f"Test failed: {e}")
