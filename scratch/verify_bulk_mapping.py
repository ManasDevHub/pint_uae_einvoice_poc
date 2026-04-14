import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app.adapters.generic_erp import GenericJSONAdapter
from app.adapters.xml_builder import generate_ubl_xml

def test_mapping():
    adapter = GenericJSONAdapter()
    
    # Simulate a raw payload from Excel
    raw_payload = {
        "invoice_number": "INV-TEST-999",
        "invoice_date": "2026-04-14",
        "transaction_type": "B2B",
        "seller_name": "Adamas Tech Consulting",
        "seller_trn": "100200300400500", # No AE prefix
        "seller_electronic_address": "accounts@adamas-tech.ae",
        "buyer_name": "Client Group FZE",
        "buyer_trn": "100999888777666", # No AE prefix
        "buyer_electronic_address": "finance@client-group.ae",
        "item_name": "Consulting Services",
        "quantity": "10",
        "unit_price": "500",
        "line_net_amount": "5000",
        "tax_amount": "250",
        "total_without_tax": "5000",
        "total_with_tax": "5250"
    }
    
    print("Transforming raw payload...")
    invoice = adapter.transform(raw_payload)
    
    print(f"Seller TRN: {invoice.seller.trn} (Expect: AE100200300400500)")
    print(f"Buyer TRN: {invoice.buyer.trn} (Expect: AE100999888777666)")
    print(f"Transaction Type Code: {invoice.transaction_type_code} (Expect: 10000000)")
    print(f"Seller Email: {invoice.seller.electronic_address} (Expect: accounts@adamas-tech.ae)")
    
    print("\nGenerating UBL XML...")
    xml = generate_ubl_xml(invoice)
    
    if 'name="10000000"' in xml:
        print("SUCCESS: Transaction Type Code found in XML.")
    else:
        print("FAILURE: Transaction Type Code missing in XML.")
        
    if 'AE100200300400500' in xml:
        print("SUCCESS: Seller TRN with AE prefix found in XML.")
    else:
        print("FAILURE: Seller TRN prefix missing in XML.")

if __name__ == "__main__":
    test_mapping()
