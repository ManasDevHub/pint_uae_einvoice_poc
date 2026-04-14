import asyncio
import httpx
import json
import sys
import os

# Mock the environment or just use requests to the live API
API_URL = "http://52.66.111.65:8000/api/v1/validate-invoice?full_pipeline=true"

SAMPLE_PAYLOAD = {
    "specification_id": "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
    "business_process_id": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
    "invoice_number": "INV-2026-001",
    "invoice_date": "2026-04-01",
    "payment_due_date": "2026-04-30",
    "invoice_type_code": "380",        
    "payment_means_type_code": "30",   
    "transaction_type": "B2B",
    "transaction_type_code": "10000000",
    "currency_code": "AED",
    "tax_category_code": "S",
    "buyer_reference": "PO-12345",
    "seller": {
        "seller_name": "Adamas Tech Corp",
        "seller_trn": "100200300400500",
        "seller_electronic_address": "accounts@adamas-tech.ae",
        "seller_electronic_scheme": "0235",
        "seller_bank_iban": "AE123456789012345678901",
        "seller_address": "Dubai Silicon Oasis",
        "seller_city": "Dubai",
        "seller_subdivision": "DU",
        "seller_country_code": "AE",
        "seller_legal_registration": "L-1002003",
        "seller_registration_identifier_type": "Trade License",
        "seller_tax_scheme_id": "VAT"
    },
    "buyer": {
        "buyer_name": "Client Group FZE",
        "buyer_trn": "100999888777666",
        "buyer_electronic_address": "finance@client-group.ae",
        "buyer_electronic_scheme": "0235",
        "buyer_address": "Abu Dhabi Global Market",
        "buyer_city": "Abu Dhabi",
        "buyer_subdivision": "AZ",
        "buyer_country_code": "AE",
        "buyer_legal_registration": "L-9988776",
        "buyer_registration_identifier_type": "Trade License",
        "buyer_tax_scheme_id": "VAT"
    },
    "lines": [{
        "line_id": "1",
        "item_name": "Consulting Services",
        "unit_of_measure": "EA",
        "quantity": 10,
        "unit_price": 500.00,
        "line_net_amount": 5000.00,
        "tax_category": "S",
        "tax_rate": 0.05,
        "tax_amount": 250.00
    }],
    "tax_subtotals": [{
        "tax_category_code": "S",
        "tax_rate": 0.05,
        "taxable_amount": 5000,
        "tax_amount": 250
    }],
    "totals": {
        "line_extension_amount": 5000.00,
        "total_without_tax": 5000.00,
        "tax_amount": 250.00,
        "total_with_tax": 5250.00,
        "amount_due": 5250.00
    }
}

async def verify():
    print(f"Verifying sample payload against {API_URL}...")
    headers = {"X-API-Key": "demo-key-123"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(API_URL, json=SAMPLE_PAYLOAD, headers=headers)
        if res.status_code == 200:
            data = res.json()
            print(f"Status: {data.get('status')}")
            print(f"Valid: {data.get('report', {}).get('is_valid')}")
            print(f"Errors: {data.get('report', {}).get('errors')}")
            print(f"Peppol Result: {data.get('message')}")
        else:
            print(f"Failed: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(verify())
