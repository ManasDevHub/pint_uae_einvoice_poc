from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, JSON, func, Text
from sqlalchemy.orm import DeclarativeBase
from uuid import uuid4

class Base(DeclarativeBase): pass

class ValidationRun(Base):
    __tablename__ = "validation_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    invoice_number = Column(String, nullable=False, index=True)
    invoice_date = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True)
    invoice_type_code = Column(String, nullable=True)
    is_valid = Column(Boolean, nullable=False)
    total_errors = Column(Integer, default=0)
    pass_percentage = Column(Float, nullable=True)
    errors_json = Column(JSON, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    status = Column(String, default="Active")
    avatar = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)   # "LOGIN", "LOGOUT", "PASSWORD_CHANGE", etc.
    success = Column(Boolean, nullable=False)
    ip_address = Column(String, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

