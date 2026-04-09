from fastapi.testclient import TestClient
from app.main import app

def test_credit_note_negative_quantity_allowed(client):
    payload = {
        "invoice_number": "CN-100",
        "invoice_date": "2026-04-01",
        "invoice_type_code": "381", # Credit Note
        "payment_means_type_code": "10",
        "currency_code": "AED",
        "tax_category_code": "S",
        "transaction_type": "B2B",
        "seller": {"seller_name": "Main Corp", "seller_trn": "123456789012345", "country_code": "AE"},
        "buyer": {"buyer_name": "Buy Co", "buyer_trn": "543210987654321", "country_code": "AE"},
        "lines": [
            {
                "line_id": "1",
                "quantity": -2, 
                "unit_of_measure": "EA",
                "unit_price": 100,
                "line_net_amount": -200,
                "tax_category": "S",
                "tax_rate": 0.05,
                "tax_amount": -10
            }
        ],
        "totals": {
            "total_without_tax": -200, "tax_amount": -10, "total_with_tax": -210, "amount_due": -210
        }
    }
    
    response = client.post("/api/v1/validate-invoice", json=payload)
    data = response.json()
    assert data["status"] == "SUCCESS", "Credit note should be fully valid."
    assert data["report"]["is_valid"] is True
    errors = data.get("report", {}).get("errors", [])
    
    high_errors = [e for e in errors if e["severity"] == "HIGH"]
    assert len(high_errors) == 0, f"Expected no HIGH errors for Credit Note, got: {high_errors}"

def test_credit_note_invalid_uom_caught(client):
    payload = {
        "invoice_number": "CN-101",
        "invoice_date": "2026-04-01",
        "invoice_type_code": "381", 
        "payment_means_type_code": "10",
        "currency_code": "AED",
        "tax_category_code": "S",
        "transaction_type": "B2B",
        "seller": {"seller_name": "Main", "seller_trn": "123456789012345", "country_code": "AE"},
        "buyer": {"buyer_name": "Buy", "buyer_trn": "123456789012345", "country_code": "AE"},
        "lines": [
            {
                "quantity": -2,
                "unit_of_measure": "INVALID_UOM", # Should trigger HIGH failure
                "unit_price": 100,
                "line_net_amount": -200,
                "tax_category": "S",
                "tax_rate": 0.05,
                "tax_amount": -10
            }
        ],
        "totals": {
            "total_without_tax": -200, "tax_amount": -10, "total_with_tax": -210, "amount_due": -210
        }
    }
    response = client.post("/api/v1/validate-invoice", json=payload)
    data = response.json()
    assert data["status"] == "FAILURE"
    assert data["report"]["is_valid"] is False
    assert "unit_of_measure" in [e["field"] for e in data["report"]["errors"]]

def test_tax_category_rate_mismatch(client):
    payload = {
        "invoice_number": "INV-TAX",
        "invoice_date": "2026-04-01",
        "invoice_type_code": "380", 
        "payment_means_type_code": "10",
        "currency_code": "AED",
        "tax_category_code": "Z", # Zero-rated
        "seller": {"seller_name": "Corp", "seller_trn": "123456789012345", "country_code": "AE"},
        "buyer": {"buyer_name": "Buy"},
        "lines": [
            {
                "quantity": 10,
                "unit_of_measure": "INVALID_UOM", # Should trigger UoM error
                "line_net_amount": 100,
                "tax_category": "Z",
                "tax_rate": 0.05, # INVALID! Z must be 0.00
                "tax_amount": 5
            }
        ],
        "totals": {
            "total_without_tax": 100, "tax_amount": 5, "total_with_tax": 105, "amount_due": 105
        }
    }
    response = client.post("/api/v1/validate-invoice", json=payload)
    data = response.json()
    assert data["report"]["is_valid"] is False
    assert data["status"] == "FAILURE"
    errors = data.get("report", {}).get("errors", [])
    error_fields = [e["field"] for e in errors]
    
    assert "tax_rate" in error_fields
    assert "tax_amount" in error_fields # Expect error because Z must have ZERO tax.
    assert "unit_of_measure" in error_fields

def test_tax_category_E_and_O(client, valid_api_payload):
    # Test 'E' category
    valid_api_payload["tax_category_code"] = "E"
    valid_api_payload["lines"][0]["tax_category"] = "E"
    valid_api_payload["lines"][0]["tax_rate"] = 0.0
    valid_api_payload["lines"][0]["tax_amount"] = 0.0
    valid_api_payload["totals"]["tax_amount"] = 0.0
    valid_api_payload["totals"]["total_with_tax"] = valid_api_payload["totals"]["total_without_tax"]
    valid_api_payload["totals"]["amount_due"] = valid_api_payload["totals"]["total_without_tax"]
    
    res = client.post("/api/v1/validate-invoice", json=valid_api_payload)
    assert res.json()["status"] == "SUCCESS"
    assert res.json()["report"]["is_valid"] is True
    
    # Test 'O' category
    valid_api_payload["tax_category_code"] = "O"
    valid_api_payload["lines"][0]["tax_category"] = "O"
    res = client.post("/api/v1/validate-invoice", json=valid_api_payload)
    assert res.json()["status"] == "SUCCESS"
    assert res.json()["report"]["is_valid"] is True
    # Z should have failed because rate was 0.05, and INVALID_UOM failed standard checking.
