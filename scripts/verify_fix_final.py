
import requests
import json

def verify():
    url = "http://localhost:8000/api/v1/validate-invoice"
    # Using a key that is in settings.py (I'll check settings.py in a moment, but demo-key-123 is what the user used)
    headers = {
        "X-API-Key": "demo-key-123",
        "Content-Type": "application/json"
    }
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

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Response Data:")
            print(json.dumps(response.json(), indent=2))
            if response.json().get("status") == "SUCCESS":
                print("✅ VERIFICATION SUCCESSFUL")
            else:
                print("❌ VERIFICATION FAILED (API returned failure)")
        else:
            print(f"❌ VERIFICATION FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    verify()
