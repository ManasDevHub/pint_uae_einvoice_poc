import pandas as pd
import json
from app.api.batch import map_excel_to_pint_ae

# Mock flat data structure coming from Excel
mock_data = [
    {
        "invoice_number": "INV-MAPPING-001",
        "invoice_date": "2026-04-01",
        "invoice_type_code": 380,  # INT as reported by user
        "seller_name": "Flat Corp LLC",
        "seller_trn": "100200300400500",
        "buyer_name": "Standard Buyer",
        "buyer_trn": "100999888777666",
        "line_1_item_name": "Services A",
        "line_1_quantity": 10,
        "line_1_unit_price": 500,
        "line_1_tax_rate": 0.05,
        "line_1_tax_category": "S",
        "line_2_item_name": "Extra B",
        "line_2_quantity": 2,
        "line_2_unit_price": 0,
        "line_2_tax_rate": 0,
        "line_2_tax_category": "Z",
        "total_without_tax": 5000,
        "tax_amount": 250,
        "total_with_tax": 5250,
        "amount_due": 5250
    }
]

df = pd.DataFrame(mock_data)

# Test Transformation
print("Starting Transformation Test...")
payloads = map_excel_to_pint_ae(df)

# Assertions
assert len(payloads) == 1, "Should have 1 payload"
p = payloads[0]

print("\n--- Resulting Payload ---")
print(json.dumps(p, indent=2))

# Verify Fix 1: Type conversion
assert isinstance(p["invoice_type_code"], str), "invoice_type_code must be string"
assert p["invoice_type_code"] == "380"

# Verify Fix 2: Nested Mapping
assert "seller" in p and p["seller"]["seller_name"] == "Flat Corp LLC"
assert "buyer" in p and p["buyer"]["buyer_name"] == "Standard Buyer"
assert len(p["lines"]) == 2, f"Should have 2 lines, got {len(p['lines'])}"
assert p["lines"][0]["item_name"] == "Services A"
assert p["lines"][1]["item_name"] == "Extra B"

# Verify Numeric conversion
assert isinstance(p["lines"][0]["quantity"], float)

print("\n✅ Verification Successful: Mapping Logic Fix confirmed!")
