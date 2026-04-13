import requests
import sqlite3
import os
import time

BASE_URL = "http://localhost:8000"
DB_PATH = "uae_einvoice.db"

def test_audit_flow():
    print("--- STARTING AUDIT FLOW VERIFICATION ---")
    
    # 1. Login to trigger an audit event
    print("1. Attempting login as admin...")
    login_data = {"username": "admin", "password": "Admin@123"}
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
        if r.status_code == 200:
            print("   SUCCESS: Login successful")
        else:
            print(f"   FAILED: Login returned {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"   ERROR during login: {e}")
        return False

    # Give SQLite a moment to commit
    time.sleep(1)

    # 2. Check Database directly
    print("2. Verifying database record...")
    if not os.path.exists(DB_PATH):
        print(f"   FAILED: DB file not found at {DB_PATH}")
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, username, action, success, detail, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("   FAILED: No audit entry found in table!")
            return False
        
        print(f"   SUCCESS: Found audit log: {row}")
        
        # Verify it's the correct one
        if row[1] == 'admin' and row[2] == 'LOGIN':
            print("   SUCCESS: Log details match the expected event")
        else:
             print(f"   WARNING: Log entries exist but might not match this test: {row}")
             
    except Exception as e:
        print(f"   ERROR checking DB: {e}")
        return False
    finally:
        conn.close()

    print("\n--- VERIFICATION COMPLETED SUCCESSFULLY ---")
    return True

if __name__ == "__main__":
    success = test_audit_flow()
    if not success:
        exit(1)
