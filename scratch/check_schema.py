from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='audit_logs'"))
    row = res.fetchone()
    if row:
        print(f"Schema: {row[0]}")
    else:
        print("Table audit_logs does not exist.")
