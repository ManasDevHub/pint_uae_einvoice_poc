import sys
import os
import json
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.validation.validator import InvoiceValidator
from app.models.invoice import InvoicePayload

def test_new_report():
    validator = InvoiceValidator()
    
    # Load B2B sample
    from frontend.src.constants.samplePayloads import SAMPLES
    payload_dict = SAMPLES['b2b']['payload']
    
    invoice = InvoicePayload(**payload_dict)
    report = validator.validate(invoice)
    
    print(f"Invoice: {report.invoice_number}")
    print(f"Is Valid: {report.is_valid}")
    print(f"Total Groups: {len(report.field_results)}")
    
    for group in report.field_results:
        print(f"\nGroup: {group.group}")
        for field in group.fields:
            status = "✓" if field.status == 'pass' else "✗"
            print(f"  {status} {field.label} [{field.pint_ref}]: {field.value}")
            if field.error:
                print(f"    ERROR: {field.error}")

if __name__ == "__main__":
    test_new_report()
