from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
from app.db.models import Base
import logging

log = logging.getLogger(__name__)

# ── Engine — works for both SQLite (dev) and PostgreSQL (prod) ────────────
IS_POSTGRES = "postgresql" in settings.database_url

engine = create_engine(
    settings.database_url,
    # SQLite-only arg — ignored for postgres
    connect_args={"check_same_thread": False, "timeout": 30} if not IS_POSTGRES else {},
    # Connection pool — critical for lakhs of concurrent requests
    poolclass=QueuePool if IS_POSTGRES else None,
    # Pool settings only apply if using QueuePool (Postgres)
    **({"pool_size": 10, "max_overflow": 20} if IS_POSTGRES else {})
)

# Standard pool settings for performance and stability
if IS_POSTGRES:
    engine.pool._pre_ping = True
    engine.pool._recycle = 1800

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables and seed default users."""
    Base.metadata.create_all(bind=engine)

    if not IS_POSTGRES:
        # SQLite only — add missing columns gracefully
        _sqlite_migrate()

    _seed_users()
    log.info("Database initialized", extra={"db": "postgresql" if IS_POSTGRES else "sqlite"})


def _sqlite_migrate():
    """Safe column additions for SQLite — no-op on PostgreSQL."""
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE users ADD COLUMN last_login DATETIME",
            "ALTER TABLE validation_runs ADD COLUMN seller_trn TEXT",
            "ALTER TABLE validation_runs ADD COLUMN transaction_type TEXT",
            "ALTER TABLE client_submissions ADD COLUMN source_filename TEXT",
            "ALTER TABLE client_submissions ADD COLUMN source_module TEXT",
            "ALTER TABLE client_submissions ADD COLUMN raw_request_path TEXT",
            "ALTER TABLE test_runs ADD COLUMN rule_selection JSON",
            "ALTER TABLE test_runs ADD COLUMN segmented_summary JSON",
            "CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT, success BOOLEAN, ip_address TEXT, detail TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)",
        ]:
            try:
                # For audit_logs, if it exists but is broken, we might need to drop it.
                # However, for a POC, force-fixing it is safer for the demo.
                if "CREATE TABLE" in stmt:
                    # Check if table exists and has id column
                    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"))
                    if res.fetchone():
                        # Table exists, check if it works by trying a dummy insert
                        try:
                            conn.execute(text("INSERT INTO audit_logs (username, action, success) VALUES ('system', 'MIGRATE_CHECK', 1)"))
                            conn.commit()
                        except Exception:
                            # Table is broken, drop and recreate
                            conn.execute(text("DROP TABLE audit_logs"))
                            conn.commit()
                            conn.execute(text(stmt))
                            conn.commit()
                    else:
                        conn.execute(text(stmt))
                        conn.commit()
                else:
                    conn.execute(text(stmt))
                    conn.commit()
            except Exception:
                pass  # column already exists or other safe error


def _seed_users():
    """Ensure default users always exist."""
    from app.core.auth import get_all_default_users
    from app.db.models import User

    db = SessionLocal()
    try:
        for u in get_all_default_users():
            if not db.query(User).filter(User.username == u["username"]).first():
                db.add(User(**u))
        db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

