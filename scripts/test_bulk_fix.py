import pandas as pd
import io
from app.adapters.generic_erp import GenericJSONAdapter

def test_flat_excel_line_mapping():
    adapter = GenericJSONAdapter()
    
    # Simulate a single row from an Excel upload (mapped to a dict)
    # This is what the template looks like
    raw_payload = {
        "invoice_number": "INV-BATCH-001",
        "invoice_date": "2026-04-01",
        "item_name": "Test Product",
        "quantity": "5",
        "unit_price": "100",
        "tax_rate": "0.05",
        "seller_name": "Test Seller",
        "buyer_name": "Test Buyer"
    }
    
    print("Testing transformation of flat Excel row...")
    try:
        invoice = adapter.transform(raw_payload)
        print(f"Success! Invoice {invoice.invoice_number} created.")
        print(f"Lines count: {len(invoice.lines)}")
        
        line = invoice.lines[0]
        print(f"Line 1: {line.item_name}, Qty: {line.quantity}, Price: {line.unit_price}")
        
        if len(invoice.lines) > 0:
            print("\nRESULT: PASSED")
        else:
            print("\nRESULT: FAILED (Empty lines)")
            
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    test_flat_excel_line_mapping()
