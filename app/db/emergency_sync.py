# app/db/emergency_sync.py
import sqlite3
import os
import sys

def sync_production_db(db_path):
    print(f"--- Starting Emergency Schema Sync: {db_path} ---")
    if not os.path.exists(db_path):
        print(f"Error: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Check validation_runs table
    cursor.execute("PRAGMA table_info(validation_runs)")
    cols = [r[1] for r in cursor.fetchall()]
    
    needed_vr = [
        ("etl_job_id", "VARCHAR(36)"),
        ("phase", "VARCHAR(20)"),
        ("error_phase", "VARCHAR(20)"),
        ("asp_status", "VARCHAR(30)"),
        ("asp_clearance_id", "VARCHAR(100)"),
        ("asp_submission_id", "VARCHAR(100)"),
        ("asp_rejection_reason", "TEXT"),
        ("asp_submitted_at", "DATETIME"),
        ("asp_latency_ms", "FLOAT")
    ]
    
    for col_name, col_type in needed_vr:
        if col_name not in cols:
            print(f"Adding column {col_name} to validation_runs...")
            try:
                cursor.execute(f"ALTER TABLE validation_runs ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Warning: Failed to add {col_name}: {e}")

    # 2. Check erp_connections table
    cursor.execute("PRAGMA table_info(erp_connections)")
    cols_erp = [r[1] for r in cursor.fetchall()]
    
    needed_erp = [
        ("sftp_username", "VARCHAR(100)"),
        ("sftp_port", "INTEGER DEFAULT 22"),
        ("sftp_path", "VARCHAR(300)"),
        ("poll_interval_minutes", "INTEGER DEFAULT 15")
    ]
    
    for col_name, col_type in needed_erp:
        if col_name not in cols_erp:
            print(f"Adding column {col_name} to erp_connections...")
            try:
                cursor.execute(f"ALTER TABLE erp_connections ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Warning: Failed to add {col_name}: {e}")

    # 3. Ensure asp_submission_logs exists
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asp_submission_logs (
                id VARCHAR(36) PRIMARY KEY,
                tenant_id VARCHAR(100) NOT NULL,
                validation_run_id VARCHAR(36),
                invoice_number VARCHAR(100),
                etl_job_id VARCHAR(36),
                asp_name VARCHAR(100),
                submission_id VARCHAR(100),
                clearance_id VARCHAR(100),
                status VARCHAR(30) NOT NULL,
                rejection_code VARCHAR(50),
                rejection_reason TEXT,
                http_status_code INTEGER,
                latency_ms FLOAT,
                request_payload JSON,
                response_payload JSON,
                submitted_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
            )
        """)
        print("Ensured asp_submission_logs table exists.")
    except Exception as e:
        print(f"Warning: Table creation error: {e}")

    # 4. Stamp Alembic version to '8831ed63d225'
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('8831ed63d225')")
        print("Stamped Alembic version to 8831ed63d225")
    except Exception as e:
        print(f"Warning: Alembic stamp error: {e}")

    conn.commit()
    conn.close()
    print("--- Emergency Sync Completed Successfully ---")

if __name__ == "__main__":
    path = "uae_einvoice.db"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    sync_production_db(path)
