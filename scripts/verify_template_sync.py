import sys
import os
import pandas as pd
import io

# Set PYTHONPATH to root
sys.path.append(os.getcwd())

from app.api.batch import SAMPLE_ROWS
from app.adapters.generic_erp import GenericJSONAdapter
from app.validation.validator import InvoiceValidator

def verify_sync():
    adapter = GenericJSONAdapter()
    validator = InvoiceValidator()
    
    print(f"Verifying {len(SAMPLE_ROWS)} sample rows from the template...")
    
    all_passed = True
    for i, row in enumerate(SAMPLE_ROWS):
        print(f"\n--- Row {i+1}: {row.get('invoice_number')} ---")
        try:
            # Transform
            invoice = adapter.transform(row)
            print(f"  Transform successful: {invoice.invoice_number}")
            
            # Validate
            report = validator.validate(invoice)
            
            if report.is_valid:
                print("  ✅ VALIDATION PASSED")
            else:
                print("  ❌ VALIDATION FAILED")
                all_passed = False
                for error in report.errors:
                    print(f"    - [{error.field}] {error.error} ({error.severity})")
                
                # Print details for debugging
                # print(f"    Raw mapped data: {invoice.model_dump()}")
        except Exception as e:
            print(f"  💥 ERROR during processing: {str(e)}")
            import traceback
            traceback.print_exc()
            all_passed = False

    if all_passed:
        print("\n✨ ALL SAMPLES ARE VALID! The template is now in sync with validation rules.")
    else:
        print("\n⚠️ SOME SAMPLES FAILED VALIDATION. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    verify_sync()
