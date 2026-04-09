import requests
import os

def test_xml_upload():
    url = "http://localhost:8000/api/v1/upload-bulk"
    # Note: Middleware is disabled in main.py, but if it were enabled, we'd need this
    headers = {"X-API-Key": "demo-key-123"} 
    
    file_path = "data/sample_invoice.xml"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    print(f"Testing single XML upload to {url}...")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/xml")}
            r = requests.post(url, headers=headers, files=files, timeout=10)
        
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            print("Success! Response:", r.json())
        else:
            print("Failed! Status:", r.status_code)
            print("Response text:", r.text)
    except Exception as e:
        print(f"Error during request: {e}")

if __name__ == "__main__":
    test_xml_upload()
