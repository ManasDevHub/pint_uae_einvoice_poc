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
    # ASP Response Tracking
    asp_submission_id   = Column(String(100),  nullable=True)   # ASP-assigned submission ID
    asp_clearance_id    = Column(String(100),  nullable=True)   # Clearance ID from FTA via ASP
    asp_status          = Column(String(30),   nullable=True)   # cleared | rejected | pending | error
    asp_rejection_reason= Column(Text,         nullable=True)   # Reason if rejected
    asp_submitted_at    = Column(DateTime(timezone=True), nullable=True)
    asp_latency_ms      = Column(Float,        nullable=True)   # Round-trip time to ASP
    phase               = Column(String(20),   nullable=True)   # phase1 | phase2 | phase3 | phase4
    error_phase         = Column(String(20),   nullable=True)   # Which phase first failed
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

    id          = Column(Integer, primary_key=True, autoincrement=True)
    username    = Column(String(100), nullable=False, index=True)
    action      = Column(String(50),  nullable=False)
    success     = Column(Boolean,     nullable=False)
    ip_address  = Column(String(50),  nullable=True)
    detail      = Column(Text,        nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_user_action", "username", "action"),
    )
# ── ERP connection tracking ────────────────────────────────────────────────
class ERPConnection(Base):
    __tablename__ = "erp_connections"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id       = Column(String(100), nullable=False, index=True)
    erp_type        = Column(String(50),  nullable=False)  # SAP | NETSUITE | DYNAMICS | SFTP | WEBHOOK | GENERIC
    display_name    = Column(String(200), nullable=False)
    status          = Column(String(20),  default="not_configured")  # not_configured | active | error | paused
    integration_mode = Column(String(30), nullable=False)  # api_push | sftp | bulk_upload | api_pull | webhook

    # API Push / Pull config
    erp_base_url    = Column(String(500), nullable=True)   # ERP's base URL (for pull mode)
    auth_type       = Column(String(30),  nullable=True)   # api_key | oauth2 | basic | token
    encrypted_credentials = Column(Text, nullable=True)    # JSON, encrypted at rest

    # Webhook config
    webhook_secret  = Column(String(100), nullable=True)   # HMAC secret for verifying inbound webhooks
    webhook_url     = Column(String(500), nullable=True)   # our endpoint they call

    # SFTP config
    sftp_host       = Column(String(300), nullable=True)
    sftp_port       = Column(Integer,     default=22)
    sftp_username   = Column(String(100), nullable=True)
    sftp_path       = Column(String(300), nullable=True)   # folder to poll

    # Pull schedule
    poll_interval_minutes = Column(Integer, default=15)
    last_sync_at    = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(20), nullable=True)   # success | error
    last_sync_count = Column(Integer,     default=0)       # invoices received in last sync

    # Field mapping
    field_mapping   = Column(JSON, nullable=True)          # maps ERP field names to PINT AE fields

    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_erp_tenant_type", "tenant_id", "erp_type"),
    )


# ── ASP Submission Log ─────────────────────────────────────────────────────
class ASPSubmissionLog(Base):
    """Tracks every single call made to the ASP (FTA gateway) per invoice."""
    __tablename__ = "asp_submission_logs"

    id                  = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id           = Column(String(100), nullable=False, index=True)
    validation_run_id   = Column(String(36), ForeignKey("validation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_number      = Column(String(100), nullable=True)
    etl_job_id          = Column(String(36), nullable=True)
    asp_name            = Column(String(100), default="UAE-ASP-Mock")  # Which ASP was used
    submission_id       = Column(String(100), nullable=True)    # ASP-assigned ID
    clearance_id        = Column(String(100), nullable=True)    # FTA clearance ID
    status              = Column(String(30),  nullable=False)   # submitted | cleared | rejected | error
    rejection_code      = Column(String(50),  nullable=True)    # ASP error code
    rejection_reason    = Column(Text,        nullable=True)    # Human-readable reason
    http_status_code    = Column(Integer,     nullable=True)    # HTTP response code from ASP
    latency_ms          = Column(Float,       nullable=True)    # Round-trip latency
    request_payload     = Column(JSON,        nullable=True)    # What we sent
    response_payload    = Column(JSON,        nullable=True)    # What ASP returned
    submitted_at        = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_asp_tenant_status", "tenant_id", "status"),
        Index("ix_asp_tenant_date",   "tenant_id", "submitted_at"),
    )


# ── System API Keys ───────────────────────────────────────────────────────
class SystemApiKey(Base):
    """Dynamically generated API keys for external ERP integrations."""
    __tablename__ = "system_api_keys"

    id          = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id   = Column(String(100), nullable=False, index=True)
    name        = Column(String(200), nullable=False)   # e.g. "Main SAP Connector"
    key_prefix  = Column(String(10),  nullable=False)   # first few chars
    hashed_key  = Column(String(128), nullable=False, index=True, unique=True)
    is_active   = Column(Boolean,     default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_syskey_tenant", "tenant_id"),
    )
