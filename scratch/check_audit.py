from app.db.session import engine
from sqlalchemy import inspect
import json

def check_db():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    if "audit_logs" in tables:
        with engine.connect() as conn:
            from sqlalchemy import text
            res = conn.execute(text("SELECT count(*) FROM audit_logs"))
            count = res.scalar()
            print(f"Audit logs count: {count}")
            
            if count > 0:
                res = conn.execute(text("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 5"))
                rows = [dict(row._mapping) for row in res]
                print(f"Recent logs: {json.dumps(rows, default=str, indent=2)}")
            else:
                print("Audit logs table is empty.")
    else:
        print("Audit logs table DOES NOT EXIST.")

if __name__ == "__main__":
    check_db()
