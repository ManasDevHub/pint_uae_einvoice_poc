import time
import pytest


@pytest.fixture
def valid_b2b_payload():
    return {
        "invoice_number": "INV-PERF-001",
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

@pytest.mark.performance
def test_single_invoice_under_100ms(client, valid_b2b_payload):
    start = time.perf_counter()
    r = client.post("/api/v1/validate-invoice", json=valid_b2b_payload)
    elapsed = (time.perf_counter() - start) * 1000
    assert r.status_code == 200
    assert elapsed < 1000, f"Validation took {elapsed:.1f}ms — exceeds SLA"

@pytest.mark.performance
def test_50_sequential_invoices_under_5s(client, valid_b2b_payload):
    import copy
    from uuid import uuid4
    start = time.perf_counter()
    for i in range(50):
        p = copy.deepcopy(valid_b2b_payload)
        p["invoice_number"] = f"PERF-{uuid4().hex[:8]}"
        r = client.post("/api/v1/validate-invoice", json=p)
        assert r.status_code == 200
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"50 invoices took {elapsed:.1f}s — exceeds 5s budget"
    print(f"\n50 invoices in {elapsed:.2f}s = {elapsed/50*1000:.1f}ms avg")
