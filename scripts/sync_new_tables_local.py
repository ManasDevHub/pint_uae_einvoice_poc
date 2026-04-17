import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import engine
from app.db.models import Base

def sync_db():
    print("Syncing new enterprise tables to local database...")
    Base.metadata.create_all(bind=engine)
    print("Success: Database schema is now up to date.")

if __name__ == "__main__":
    sync_db()
