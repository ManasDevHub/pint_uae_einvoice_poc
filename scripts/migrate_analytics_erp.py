# scripts/migrate_analytics_erp.py
import sqlite3
import os

DB_PATH = "app/db/uae_einvoice.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables_to_update = [
        "client_submissions",
        "submission_field_metrics",
        "validation_runs"
    ]

    for table in tables_to_update:
        try:
            print(f"Checking table {table} for connection_id...")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "connection_id" not in columns:
                print(f"Adding connection_id to {table}...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN connection_id VARCHAR(36)")
                print(f"Successfully added connection_id to {table}")
            else:
                print(f"connection_id already exists in {table}")
        except Exception as e:
            print(f"Error updating table {table}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
