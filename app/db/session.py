from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import Base

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _migrate_db():
    """Safe schema migrations for SQLite — adds new columns without dropping existing data."""
    with engine.connect() as conn:
        # Add last_login column to users if it doesn't exist
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
            conn.commit()
        except Exception:
            pass  # Column already exists — that's fine

def init_db():
    Base.metadata.create_all(bind=engine)  # Creates new tables (audit_logs, etc.)
    _migrate_db()  # Adds missing columns to existing tables
    
    # Seed initial users — ensure all default users always exist
    from app.core.auth import get_all_default_users
    from app.db.models import User
    db = SessionLocal()
    try:
        for u in get_all_default_users():
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                db.add(User(**u))
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
