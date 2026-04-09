import requests
import json
import time

url = "https://erasable-contributively-jann.ngrok-free.dev/api/v1/validate-invoice"
headers = {
    "X-API-Key": "demo-key-123",
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

payload = {
    "specification_id": "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
    "business_process_id": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
    "invoice_number": f"INV-PINT-51-{int(time.time())}",
    "invoice_date": "2026-03-26",
    "payment_due_date": "2026-04-26",
    "invoice_type_code": "380",
    "payment_means_type_code": "30",
    "transaction_type": "B2B",
    "transaction_type_code": "10000000",
    "currency_code": "AED",
    "tax_category_code": "S",
    "seller": {
        "seller_name": "Adamas Tech Consulting",
        "seller_trn": "100123456789001",
        "address": "Business Bay, Tower A",
        "city": "Dubai",
        "subdivision": "DU",
        "country_code": "AE",
        "electronic_address": "100123456789001",
        "electronic_scheme": "0235",
        "legal_registration": "1234567",
        "registration_identifier_type": "CRN",
        "tax_scheme_id": "VAT"
    },
    "buyer": {
        "buyer_name": "Digital Solutions LLC",
        "buyer_trn": "100987654321009",
        "address": "Downtown Dubai",
        "city": "Dubai",
        "subdivision": "DU",
        "country_code": "AE",
        "electronic_address": "100987654321009",
        "electronic_scheme": "0235",
        "legal_registration": "9876543",
        "registration_identifier_type": "CRN",
        "tax_scheme_id": "VAT"
    },
    "lines": [
        {
            "line_id": "1",
            "item_name": "Cloud Implementation Services",
            "item_description": "PINT AE Compliance Setup",
            "unit_of_measure": "HUR",
            "quantity": 10.0,
            "unit_price": 500.0,
            "gross_price": 500.0,
            "base_qty": 1.0,
            "line_net_amount": 5000.0,
            "tax_category": "S",
            "tax_rate": 0.05,
            "tax_amount": 250.0
        }
    ],
    "totals": {
        "total_without_tax": 5000.0,
        "tax_amount": 250.0,
        "total_with_tax": 5250.0,
        "amount_due": 5250.0
    }
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=5)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
