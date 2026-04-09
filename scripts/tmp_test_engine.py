
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.rules_engine import RuleEngine
from app.models.invoice import InvoicePayload
from app.adapters.generic_erp import GenericJSONAdapter

def test_engine():
    rules_path = os.path.join(os.getcwd(), "rules", "uae_pint_ae_rules.json")
    engine = RuleEngine(rules_path)
    
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
    
    adapter = GenericJSONAdapter()
    invoice = adapter.transform(payload)
    flat_data = invoice.extract_flat_data()
    print(f"Flat Data keys: {list(flat_data.keys())}")
    
    errors = engine.evaluate(flat_data)
    print(f"Rule Engine Errors: {[e.field for e in errors]}")
    
    assert "tax_category_code" in [e.field for e in errors]
    assert "payment_means_type_code" in [e.field for e in errors]
    assert "seller_country_code" in [e.field for e in errors]

if __name__ == "__main__":
    try:
        test_engine()
        print("Engine test passed!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Engine test failed: {e}")
