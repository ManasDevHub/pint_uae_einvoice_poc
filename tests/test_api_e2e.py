from fastapi.testclient import TestClient
from app.main import app
import pytest

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"

def test_full_successful_invoice(client, valid_api_payload):
    import uuid
    valid_api_payload["invoice_number"] = f"INV-E2E-{uuid.uuid4().hex[:6]}"
    response = client.post("/api/v1/validate-invoice", json=valid_api_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS", f"Expected SUCCESS, got errors: {data.get('report', {}).get('errors')}"
    assert data["report"]["metrics"]["pass_percentage"] == 100.0
    assert data["report"]["metrics"]["failed_checks"] == 0

def test_empty_payload_bug_hunt(client):
    """
    If we submit an empty payload, it should ideally fail gracefully and detect missing mandatory rules.
    """
    response = client.post("/api/v1/validate-invoice", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "FAILURE"
    errors = data["report"]["errors"]
    
    # Missing required elements should be flagged by Pydantic schema validation!
    error_fields = [e["field"] for e in errors]
    assert "invoice_number" in error_fields
    assert "invoice_date" in error_fields
    assert "lines" in error_fields

def test_b2b_vs_b2c_adapter_inference(client):
    """
    If buyer_trn is missing, adapter assumes B2C. For B2C, buyer_trn is NOT required.
    """
    payload = {
        "invoice_number": "INV-100",
        "invoice_date": "2026-04-01",
        "invoice_type_code": "380",
        "payment_means_type_code": "10",
        "currency_code": "AED",
        "tax_category_code": "S",
        "seller": {
            "seller_name": "Main Corp",
            "seller_trn": "123456789012345"
        },
        "buyer": {
            "buyer_name": "Buy Co"
        },
        "lines": [
            {"line_net_amount": 100, "tax_amount": 5}
        ],
        "totals": {
            "total_without_tax": 100, "tax_amount": 5, "total_with_tax": 105, "amount_due": 105
        }
    }
    response = client.post("/api/v1/validate-invoice", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS", "B2C inference failed and tripped conditional rule"
    assert "buyer_trn" not in [e["field"] for e in data["report"]["errors"]]
    
def test_asp_mock_endpoints(client, valid_api_payload):
    response = client.post("/asp/v1/validate", json=valid_api_payload)
    assert response.status_code == 200
    assert response.json()["asp_status"] == "ACCEPTED"
    assert "invoice_number" in response.json()
    
    response = client.post("/asp/v1/submit", json=valid_api_payload)
    assert response.status_code == 200
    assert response.json()["asp_status"] == "CLEARED"
    assert "clearance_id" in response.json()

def test_group_e_negative_scenarios(client):
    payload = {
        "invoice_number": "INV-E2E-099",
        "invoice_date": "2026-04-01",
        "invoice_type_code": "380",
        "currency_code": "AED",
        "payment_means_type_code": "999", # E4 Invalid Payment Means (Fail)
        "tax_category_code": "X", # E4 Invalid Tax Category (Fail)
        "seller": {
            "seller_name": "Main Corp",
            "seller_trn": "123456789012345",
            "country_code": "US" # E - Invalid Seller Country (Fail)
        },
        "buyer": {"buyer_name": "Buy Co"}, # B2C inferred
        "lines": [
            {
                "quantity": -5, 
                "unit_of_measure": "EA",
                "line_net_amount": 100, 
                "tax_category": "S", 
                "tax_rate": 0.05,
                "tax_amount": 9.99 
            }
        ],
        "totals": {
            "total_without_tax": 100, "tax_amount": 5, "total_with_tax": 105, "amount_due": 105
        }
    }
    
    response = client.post("/api/v1/validate-invoice", json=payload)
    data = response.json()
    assert data["status"] == "FAILURE"
    assert data["report"]["is_valid"] is False
    
    errors = [e["field"] for e in data["report"]["errors"]]
    assert "tax_category_code" in errors
    assert "payment_means_type_code" in errors
    assert "seller_country_code" in errors
    assert "quantity" in errors
    assert "invoiced_item_tax_category" in errors
    assert "tax_amount" in errors

def test_fastapi_schema_422(client):
    response = client.post("/api/v1/validate-invoice", content="Mal-formed-string")
    assert response.status_code == 422
