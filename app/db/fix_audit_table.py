import sqlite3
import os

def fix_audit_table():
    db_path = "uae_einvoice.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    print(f"Targeting database: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 1. Drop old table
        print("Dropping old audit_logs table (if it exists)...")
        cur.execute("DROP TABLE IF EXISTS audit_logs")
        
        # 2. Recreate table with exact schema from models.py
        # Note: Integer PRIMARY KEY handles AUTOINCREMENT in SQLite
        print("Creating fresh audit_logs table with correct schema...")
        cur.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                action VARCHAR(50) NOT NULL,
                success BOOLEAN NOT NULL,
                ip_address VARCHAR(50),
                detail TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Create indexes
        print("Creating indexes...")
        cur.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)")
        cur.execute("CREATE INDEX ix_audit_logs_username ON audit_logs (username)")
        cur.execute("CREATE INDEX ix_audit_user_action ON audit_logs (username, action)")
        
        conn.commit()
        print("Migration COMPLETED SUCCESSFULY.")
        
    except Exception as e:
        print(f"Migration FAILED: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_audit_table()
