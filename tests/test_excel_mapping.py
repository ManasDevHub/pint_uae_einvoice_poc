from app.adapters.generic_erp import GenericJSONAdapter

def test_adapter_handle_test_placeholders():
    # Mock data with 'TEST' strings in numeric fields
    mock_row = {
        "invoice_number": "INV-1001",
        "invoice_date": "2026-04-01",
        "quantity": "TEST",
        "unit_price": "TEST",
        "total_with_tax": "TEST",
        "tax_rate": "TEST",
        "invoice_type_code": "TEST"
    }
    
    adapter = GenericJSONAdapter()
    p = adapter.transform(mock_row)
    
    # Verify Fix: No crash + Defaulting
    assert p.lines[0].quantity == 0.0
    assert p.lines[0].unit_price == 0.0
    assert p.totals.total_with_tax == 0.0
    assert p.lines[0].tax_rate == 0.05 # Default for tax_rate
    assert p.invoice_type_code == "380" # Default for type code

def test_adapter_robustness_flat_data():
    # Mock data with reported edge cases
    mock_row = {
        "invoice_number": "INV-ADAPTER-001",
        "invoice_date": "2026-04-01",
        "invoice_type_code": 380,  # INT code to be converted
        "seller_name": "Test Seller LLC",
        "seller_trn": "100200300400500",
        "buyer_name": "Test Buyer",
        "buyer_trn": "100999888777666",
        "line_1_item_name": "Services A",
        "line_1_quantity": 10.0,
        "line_1_unit_price": 500.0,
        "line_1_tax_rate": 0.05,
        "line_1_tax_category": "S",
        "line_2_item_name": "Product B",
        "line_2_quantity": 2.0,
        "line_2_unit_price": 100.0,
        "line_2_tax_rate": 0.05,
        "line_2_tax_category": "S",
        "total_without_tax": 5200.0,
        "tax_amount": 260.0,
        "total_with_tax": 5460.0,
        "amount_due": 5460.0
    }
    
    adapter = GenericJSONAdapter()
    p = adapter.transform(mock_row) # This returns InvoicePayload
    
    # 1. Type Check
    assert isinstance(p.invoice_type_code, str)
    assert p.invoice_type_code == "380"
    
    # 2. Nested Structure Check
    assert p.seller.name == "Test Seller LLC"
    assert p.buyer.name == "Test Buyer"
    
    # 3. Lines Array Check
    assert len(p.lines) == 2
    assert p.lines[0].item_name == "Services A"
    assert p.lines[1].item_name == "Product B"
    assert p.lines[0].quantity == 10.0
    
    # 4. Totals Grouping
    assert p.totals.total_with_tax == 5460.0

def test_adapter_single_unnamed_line():
    # Case where line columns are NOT prefixed (e.g. just quantity, unit_price)
    mock_row = {
        "invoice_number": "INV-SINGLE-001",
        "invoice_date": "2026-04-01",
        "item_name": "Standalone Service",
        "quantity": 1,
        "unit_price": 1000
    }
    
    adapter = GenericJSONAdapter()
    p = adapter.transform(mock_row)
    
    assert len(p.lines) == 1
    assert p.lines[0].item_name == "Standalone Service"
    assert p.lines[0].quantity == 1.0
