import requests
import json

url = "http://52.66.111.65:8000/api/v1/validate-invoice?full_pipeline=true"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "demo-key-123"
}

payload = {
  "specification_id": "urn:peppol:pint:billing-1.0:ae:en:1.0",
  "business_process_id": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
  "invoice_number": "INV-PROD-TEST-999",
  "invoice_date": "2026-04-01",
  "payment_due_date": "2026-04-15",
  "invoice_type_code": "380",
  "payment_means_type_code": "30",
  "transaction_type": "B2B",
  "transaction_type_code": "10000000",
  "currency_code": "AED",
  "tax_category_code": "S",
  "seller": {
    "seller_name": "Adamas Tech Consulting LLC",
    "seller_trn": "100200300400500",
    "seller_electronic_address": "pos@adamas-tech.ae",
    "seller_electronic_scheme": "0235",
    "seller_legal_registration": "DED-123",
    "seller_registration_identifier_type": "0235",
    "seller_address": "Dubai Mall",
    "seller_city": "Dubai",
    "seller_subdivision": "AE-DU",
    "seller_country_code": "AE",
    "seller_tax_scheme_id": "VAT"
  },
  "buyer": {
    "buyer_name": "Elite Retail Group",
    "buyer_trn": "100900800700600",
    "buyer_electronic_address": "procurement@elite-retail.ae",
    "buyer_electronic_scheme": "0235",
    "buyer_legal_registration": "DED-456",
    "buyer_registration_identifier_type": "0235",
    "buyer_address": "Abu Dhabi Mall",
    "buyer_city": "Abu Dhabi",
    "buyer_subdivision": "AE-AZ",
    "buyer_country_code": "AE",
    "buyer_tax_scheme_id": "VAT"
  },
  "lines": [
    {
      "line_id": "1",
      "item_name": "Premium Tech Consultant Fee",
      "quantity": 1.0,
      "unit_of_measure": "EA",
      "unit_price": 1000.0,
      "line_net_amount": 1000.0,
      "tax_category": "S",
      "tax_rate": 0.05,
      "tax_amount": 50.0
    }
  ],
  "totals": {
    "line_extension_amount": 1000.0,
    "total_without_tax": 1000.0,
    "total_with_tax": 1050.0,
    "tax_amount": 50.0,
    "amount_due": 1050.0
  },
  "tax_subtotals": [
    {
      "taxable_amount": 1000.0,
      "tax_amount": 50.0,
      "tax_category_code": "S",
      "tax_rate": 0.05
    }
  ]
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
