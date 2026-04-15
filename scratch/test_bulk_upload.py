import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_bulk_upload():
    # 1. Start backend if not running (assumes it's running for the test)
    
    # 2. Prepare multi-line CSV
    csv_content = """invoice_number,invoice_date,payment_due_date,invoice_type_code,payment_means_type_code,payment_terms,transaction_type,transaction_type_code,currency_code,tax_category_code,buyer_reference,specification_id,business_process_id,seller_name,seller_trn,seller_electronic_address,seller_electronic_scheme,seller_bank_iban,seller_address,seller_city,seller_subdivision,seller_country_code,seller_legal_registration,seller_registration_identifier_type,buyer_name,buyer_trn,buyer_electronic_address,buyer_electronic_scheme,buyer_address,buyer_city,buyer_subdivision,buyer_country_code,buyer_legal_registration,buyer_registration_identifier_type,line_id,item_name,item_description,unit_of_measure,quantity,unit_price,line_net_amount,tax_category,tax_rate,tax_amount,total_without_tax,total_with_tax,amount_due
INV-MULTI-001,2026-04-01,2026-04-30,380,30,Standard 30 Days,B2B,10000000,AED,S,REF-001,urn:peppol:pint:billing-1.0:ae:en:1.0,urn:fdc:peppol.eu:2017:poacc:billing:01:1.0,Adamas Tech,100200300400500,accounts@adamas-tech.ae,0235,AE070331234567890123456,Dubai,Dubai,DU,AE,L-1002003,Trade License,Client FZE,100999888777666,finance@client-group.ae,0235,Abu Dhabi,Abu Dhabi,AZ,AE,L-9988776,Trade License,1,Consulting,IT Strategy,EA,10,500,5000,S,0.05,250,7000,7350,350,7000,7350,7350
INV-MULTI-001,2026-04-01,2026-04-30,380,30,Standard 30 Days,B2B,10000000,AED,S,REF-001,urn:peppol:pint:billing-1.0:ae:en:1.0,urn:fdc:peppol.eu:2017:poacc:billing:01:1.0,Adamas Tech,100200300400500,accounts@adamas-tech.ae,0235,AE070331234567890123456,Dubai,Dubai,DU,AE,L-1002003,Trade License,Client FZE,100999888777666,finance@client-group.ae,0235,Abu Dhabi,Abu Dhabi,AZ,AE,L-9988776,Trade License,2,Hardware,Server Rack,EA,1,2000,2000,S,0.05,100,7000,7350,350,7000,7350,7350
"""
    headers = {'X-API-Key': 'demo-key-123'}
    files = {'file': ('test_multi_line.csv', csv_content, 'text/csv')}
    
    print("Uploading bulk CSV...")
    response = requests.post(f"{BASE_URL}/ingest-bulk", files=files, headers=headers)
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
    
    res_data = response.json()
    batch_id = res_data["batch_id"]
    print(f"Batch created: {batch_id}")
    
    # 3. Poll for status
    for _ in range(10):
        time.sleep(2)
        status_res = requests.get(f"{BASE_URL}/batch-status/{batch_id}", headers=headers)
        status_data = status_res.json()
        print(f"DEBUG: {status_data}")
        
        status = status_data.get('status', 'PENDING')
        done = status_data.get('done', 0)
        total = status_data.get('total', 0)
        
        print(f"Status: {status} ({done}/{total})")
        
        if status in ["COMPLETE", "PARTIAL", "FAILED"]:
            break
            
    print("\nFinal Results:")
    print(json.dumps(status_data, indent=2))
    
    if status == "COMPLETE" and status_data.get("valid") == 1:
        print("\nVerification SUCCESS: Multi-line invoice processed correctly.")
    else:
        print("\nVerification FAILED: Check logs.")

if __name__ == "__main__":
    test_bulk_upload()
