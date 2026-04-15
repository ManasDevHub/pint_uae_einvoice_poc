"""
Safe schema migration for production.
Uses ALTER TABLE IF NOT EXISTS pattern - safe to run multiple times.
"""
import sqlite3
import os

DB_PATH = "/home/ubuntu/uae_invoice/uae_einvoice.db"

# Columns to add to validation_runs if they don't exist
NEW_COLUMNS = [
    ("validation_runs", "asp_submission_id",    "TEXT"),
    ("validation_runs", "asp_clearance_id",     "TEXT"),
    ("validation_runs", "asp_status",           "TEXT DEFAULT 'PENDING'"),
    ("validation_runs", "asp_rejection_reason", "TEXT"),
    ("validation_runs", "asp_submitted_at",     "DATETIME"),
    ("validation_runs", "asp_latency_ms",       "REAL"),
    ("validation_runs", "phase",                "TEXT DEFAULT 'submitted'"),
    ("validation_runs", "error_phase",          "TEXT"),
    ("etl_jobs",        "source_type",          "TEXT DEFAULT 'csv'"),
    ("etl_jobs",        "total_rows",           "INTEGER DEFAULT 0"),
    ("etl_jobs",        "processed_rows",       "INTEGER DEFAULT 0"),
    ("etl_jobs",        "failed_rows",          "INTEGER DEFAULT 0"),
]

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

for table, col, coltype in NEW_COLUMNS:
    # Check if column already exists
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    if col not in existing:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
            print(f"  [ADDED] {table}.{col}")
        except Exception as e:
            print(f"  [SKIP]  {table}.{col}: {e}")
    else:
        print(f"  [OK]    {table}.{col} already exists")

# Create system_api_keys table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS system_api_keys (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL,
    name         TEXT NOT NULL,
    key_prefix   TEXT NOT NULL,
    hashed_key   TEXT NOT NULL UNIQUE,
    is_active    INTEGER DEFAULT 1,
    last_used_at DATETIME,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("  [OK]    system_api_keys table ensured")

conn.commit()
conn.close()
print("\nMigration complete. All checks passed.")
