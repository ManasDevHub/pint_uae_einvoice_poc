import requests
import json

def test_batch_validate_fix():
    url = "http://localhost:8000/api/v1/batch-validate"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "demo-key-123"
    }
    
    # 2 invoices: 1 good, 1 bad
    payloads = [
        {
            "invoice_number": "INV-GOOD",
            "invoice_date": "2026-04-01",
            "transaction_type": "B2B",
            "seller": {"name": "S1", "trn": "100200300400500"},
            "buyer": {"name": "B1", "trn": "100999888777666"},
            "lines": [{"item_name": "P1", "quantity": 1, "unit_price": 100}]
        },
        {
            "invoice_number": "INV-BAD",
            "invoice_date": "2026-04-01",
            "transaction_type": "B2B",
            "seller": {"name": "S1", "trn": "123"}, # Bad TRN
            "buyer": {"name": "B1", "trn": "456"},    # Bad TRN
            "lines": [] # Missing lines
        }
    ]
    
    print("Testing /api/v1/batch-validate...")
    response = requests.post(url, headers=headers, json=payloads)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    data = response.json()
    batch_id = data['batch_id']
    print(f"Batch Accepted: {batch_id}")
    
    # Poll for status
    import time
    for _ in range(5):
        time.sleep(2)
        res = requests.get(f"http://localhost:8000/api/v1/batch-status/{batch_id}", headers=headers)
        if res.status_code == 200:
            status_data = res.json()
            print(f"Status: {status_data['status']} ({status_data['done']}/{status_data['total']})")
            if status_data['status'] == 'COMPLETE':
                results = status_data['results']
                for r in results:
                    print(f"\nInvoice {r['invoice_number']}: {'PASSED' if r['is_valid'] else 'FAILED'}")
                    if not r['is_valid']:
                        print(f"Errors found: {len(r['errors'])}")
                        # Check if field_results exists in the result
                        if 'field_results' in r:
                            print(f"Detail check: Found field_results with {len(r['field_results'])} groups.")
                break

if __name__ == "__main__":
    test_batch_validate_fix()
