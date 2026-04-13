from sqlalchemy import (
    Column, String, Boolean, Integer, Float, DateTime,
    JSON, Text, Index, BigInteger, Enum, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from uuid import uuid4
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────
class InvoiceStatus(str, enum.Enum):
    PENDING    = "PENDING"
    PROCESSING = "PROCESSING"
    VALID      = "VALID"
    INVALID    = "INVALID"
    FAILED     = "FAILED"     # system error, not validation failure

class ETLJobStatus(str, enum.Enum):
    QUEUED     = "QUEUED"
    RUNNING    = "RUNNING"
    COMPLETE   = "COMPLETE"
    FAILED     = "FAILED"
    PARTIAL    = "PARTIAL"    # some rows failed


# ── Core validation table ─────────────────────────────────────────────────
class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id                  = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id           = Column(String(100), nullable=False, index=True)
    invoice_number      = Column(String(100), nullable=False, index=True)
    invoice_date        = Column(String(20),  nullable=True)
    transaction_type    = Column(String(10),  nullable=True)
    invoice_type_code   = Column(String(10),  nullable=True)
    seller_trn          = Column(String(20),  nullable=True)
    buyer_trn           = Column(String(20),  nullable=True)
    seller_name         = Column(String(200), nullable=True)
    buyer_name          = Column(String(200), nullable=True)
    currency_code       = Column(String(5),   nullable=True)
    tax_category_code   = Column(String(5),   nullable=True)
    total_with_tax      = Column(Float,        nullable=True)
    is_valid            = Column(Boolean,      nullable=False, index=True)
    total_errors        = Column(Integer,      default=0)
    total_checks        = Column(Integer,      default=0)
    pass_percentage     = Column(Float,        nullable=True)
    errors_json         = Column(JSON,         nullable=True)
    field_results_json  = Column(JSON,         nullable=True)   # field-by-field breakdown
    raw_payload         = Column(JSON,         nullable=True)
    duration_ms         = Column(Float,        nullable=True)
    source              = Column(String(50),   default="api")   # api | excel | xml | etl
    etl_job_id          = Column(String(36),   ForeignKey("etl_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    etl_job = relationship("ETLJob", back_populates="validation_runs")

    __table_args__ = (
        Index("ix_vr_tenant_created", "tenant_id", "created_at"),
        Index("ix_vr_tenant_valid",   "tenant_id", "is_valid"),
        Index("ix_vr_invoice_num",    "invoice_number", "tenant_id"),
    )


# ── ETL job tracking ──────────────────────────────────────────────────────
class ETLJob(Base):
    __tablename__ = "etl_jobs"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    batch_id        = Column(String(50), nullable=False, unique=True, index=True)
    tenant_id       = Column(String(100), nullable=False, index=True)
    job_type        = Column(String(50),  default="bulk_excel")  # bulk_excel | api_batch | xml_zip | sftp
    source_filename = Column(String(255), nullable=True)
    source_format   = Column(String(20),  nullable=True)         # excel | csv | xml | json
    status          = Column(String(20),  default=ETLJobStatus.QUEUED.value)
    total_rows      = Column(Integer,     default=0)
    processed_rows  = Column(Integer,     default=0)
    valid_rows      = Column(Integer,     default=0)
    invalid_rows    = Column(Integer,     default=0)
    failed_rows     = Column(Integer,     default=0)   # system errors
    error_message   = Column(Text,        nullable=True)
    started_at      = Column(DateTime(timezone=True), nullable=True)
    completed_at    = Column(DateTime(timezone=True), nullable=True)
    duration_ms     = Column(Float,       nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    validation_runs = relationship("ValidationRun", back_populates="etl_job")

    __table_args__ = (
        Index("ix_etl_tenant_status", "tenant_id", "status"),
        Index("ix_etl_created",       "created_at"),
    )


# ── ETL row-level errors (separate from validation errors) ────────────────
class ETLRowError(Base):
    __tablename__ = "etl_row_errors"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    etl_job_id  = Column(String(36), ForeignKey("etl_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number  = Column(Integer,    nullable=False)
    invoice_number = Column(String(100), nullable=True)
    error_type  = Column(String(50),  nullable=False)   # SCHEMA | PARSE | VALIDATION | SYSTEM
    error_message = Column(Text,      nullable=False)
    raw_data    = Column(JSON,        nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


# ── Users ─────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(100), unique=True, index=True, nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    full_name       = Column(String(200), nullable=False)
    role            = Column(String(50),  nullable=False)
    hashed_password = Column(String(255), nullable=False)
    status          = Column(String(20),  default="Active")
    avatar          = Column(String(10),  nullable=True)
    last_login      = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


# ── Audit log ─────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    username    = Column(String(100), nullable=False, index=True)
    action      = Column(String(50),  nullable=False)
    success     = Column(Boolean,     nullable=False)
    ip_address  = Column(String(50),  nullable=True)
    detail      = Column(Text,        nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_user_action", "username", "action"),
    )
