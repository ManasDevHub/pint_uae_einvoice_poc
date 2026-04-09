
import json
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.adapters.generic_erp import GenericJSONAdapter
from app.validation.validator import InvoiceValidator
from app.models.invoice import InvoicePayload

def test_reproduce():
    payload = {
      "invoice_number": "INV-2026-AE-001",
      "invoice_date": "2026-04-01",
      "payment_due_date": "2026-04-30",
      "invoice_type_code": "380",
      "payment_means_type_code": "10",
      "transaction_type": "B2B",
      "currency_code": "AED",
      "tax_category_code": "S",
      "seller": {
        "seller_name": "Adamas Tech Consulting LLC",
        "seller_trn": "100200300400500",
        "seller_electronic_address": "accounts@adamas-tech.ae",
        "seller_legal_registration": "DED-2024-12345",
        "seller_registration_identifier_type": "DED",
        "seller_address": "Dubai Internet City, Dubai, UAE",
        "seller_city": "Dubai",
        "seller_subdivision": "DU",
        "seller_country_code": "AE"
      },
      "buyer": {
        "buyer_name": "Gulf Trading FZE",
        "buyer_trn": "100999888777666",
        "buyer_electronic_address": "finance@gulftrade.ae",
        "buyer_legal_registration": "ADGM-2023-67890",
        "buyer_registration_identifier_type": "ADGM",
        "buyer_address": "Abu Dhabi, UAE",
        "buyer_city": "Abu Dhabi",
        "buyer_subdivision": "AZ",
        "buyer_country_code": "AE"
      },
      "lines": [
        {
          "line_id": "1",
          "item_name": "ERP Consulting Services",
          "unit_of_measure": "EA",
          "quantity": 10,
          "unit_price": 500,
          "line_net_amount": 5000,
          "tax_category": "S",
          "tax_rate": 0.05,
          "tax_amount": 250
        }
      ],
      "tax_subtotals": [
        {
          "tax_category_code": "S",
          "tax_rate": 0.05,
          "taxable_amount": 5000,
          "tax_amount": 250
        }
      ],
      "totals": {
        "line_extension_amount": 5000,
        "total_without_tax": 5000,
        "tax_amount": 250,
        "total_with_tax": 5250,
        "amount_due": 5250
      }
    }

    print("Starting transformation...")
    adapter = GenericJSONAdapter()
    invoice = adapter.transform(payload)
    print("Transformation successful.")
    print(f"Transformed Totals: {invoice.totals.model_dump()}")

    print("Starting validation...")
    validator = InvoiceValidator()
    report = validator.validate(invoice)
    print("Validation successful.")
    
    # print(report.model_dump_json(indent=2))

if __name__ == "__main__":
    try:
        test_reproduce()
        print("Test passed! No crash.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Test failed with error: {e}")
