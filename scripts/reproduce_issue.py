import pandas as pd
import io
from app.api.batch import TEMPLATE_COLUMNS, SAMPLE_ROWS
from app.adapters.generic_erp import GenericJSONAdapter
from app.validation.validator import InvoiceValidator

def reproduce_issue():
    # 1. Simulate "Download" (getting data structure)
    # Note: In reality, pandas reads the excel. Here we just use the SAMPLE_ROWS.
    
    adapter = GenericJSONAdapter()
    validator = InvoiceValidator()
    
    print(f"Testing with {len(SAMPLE_ROWS)} sample rows...")
    
    for i, row in enumerate(SAMPLE_ROWS):
        print(f"\n--- Row {i+1} ({row.get('invoice_number')}) ---")
        try:
            # The adapter expects a dict which represents a row in Excel (normalized keys handled inside)
            invoice = adapter.transform(row)
            report = validator.validate(invoice)
            
            if report.is_valid:
                print("✅ VALID")
            else:
                print("❌ INVALID")
                for error in report.errors:
                    print(f"  - [{error.field}] {error.error} ({error.severity})")
        except Exception as e:
            print(f"💥 TRANSFORM ERROR: {str(e)}")

if __name__ == "__main__":
    reproduce_issue()
