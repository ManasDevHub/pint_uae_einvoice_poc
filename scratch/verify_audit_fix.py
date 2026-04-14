import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal, init_db
from app.api.auth_router import _log_audit
from app.db.models import AuditLog
from sqlalchemy import desc

def verify_audit():
    print("Initialising DB...")
    init_db()
    
    db = SessionLocal()
    try:
        print("Logging a test event...")
        _log_audit(db, "test_user", "VERIFY_TEST", True, detail="Verifying audit log fix")
        
        print("Checking recent logs...")
        logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(1).all()
        if logs and logs[0].action == "VERIFY_TEST":
            print(f"SUCCESS: Found log entry: {logs[0].username} - {logs[0].action} - {logs[0].detail}")
        else:
            print("FAILURE: Log entry not found or mismatch.")
    finally:
        db.close()

if __name__ == "__main__":
    verify_audit()
