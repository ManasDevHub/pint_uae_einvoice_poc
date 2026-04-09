import pytest
import os
from uuid import uuid4
os.environ["API_KEYS"] = "test-key-123"

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_env():
    os.environ["API_KEYS"] = "test-key-123"

@pytest.fixture(scope="session")
def client():
    c = TestClient(app)
    c.headers.update({"X-API-Key": "test-key-123"})
    return c

@pytest.fixture
def invoice_id():
    """Unique invoice number per test run — prevents duplicate detection false positives."""
    return f"INV-TEST-{uuid4().hex[:8].upper()}"

@pytest.fixture
def valid_b2b_payload(invoice_id):
    return {
        "invoice_number": invoice_id,
        "invoice_date": "2026-04-01",
        "invoice_type_code": "380",
        "payment_means_type_code": "10",
        "transaction_type": "B2B",
        "currency_code": "AED",
        "tax_category_code": "S",
        "seller": {"seller_name": "Tech Corp LLC",
                   "seller_trn": "100200300400500",
                   "country_code": "AE"},
        "buyer":  {"buyer_name": "Client Group",
                   "buyer_trn": "100999888777666",
                   "country_code": "AE"},
        "lines": [{
            "line_id": "1", "item_name": "Consulting",
            "unit_of_measure": "EA", "quantity": 10,
            "unit_price": 500, "line_net_amount": 5000,
            "tax_category": "S", "tax_rate": 0.05, "tax_amount": 250
        }],
        "totals": {"total_without_tax": 5000, "tax_amount": 250,
                   "total_with_tax": 5250, "amount_due": 5250}
    }

@pytest.fixture
def valid_b2c_payload(valid_b2b_payload, invoice_id):
    import copy
    p = copy.deepcopy(valid_b2b_payload)
    p["invoice_number"] = f"B2C-{invoice_id}"
    p["transaction_type"] = "B2C"
    p["buyer"] = {"buyer_name": "Individual", "country_code": "AE"}
    # buyer TRN removed
    return p

@pytest.fixture
def valid_api_payload(valid_b2b_payload):
    return valid_b2b_payload

@pytest.fixture
def valid_invoice(valid_b2b_payload):
    from app.models.invoice import InvoicePayload
    return InvoicePayload(**valid_b2b_payload)

@pytest.fixture
def valid_b2c_invoice(valid_b2c_payload):
    from app.models.invoice import InvoicePayload
    return InvoicePayload(**valid_b2c_payload)
