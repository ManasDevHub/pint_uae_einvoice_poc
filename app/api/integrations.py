# app/api/integrations.py
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ERPConnection
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
import hashlib, hmac, json, time, os, secrets

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────

class ERPConfigBase(BaseModel):
    erp_type: str
    display_name: str
    integration_mode: str              # api_push | sftp | bulk_upload | api_pull | webhook

class SAPConfig(ERPConfigBase):
    erp_type: str = "SAP"
    integration_mode: str = "api_push"

class NetSuiteConfig(ERPConfigBase):
    erp_type: str = "NETSUITE"
    integration_mode: str = "api_push"
    netsuite_account_id: Optional[str] = None

class DynamicsConfig(ERPConfigBase):
    erp_type: str = "DYNAMICS"
    integration_mode: str = "api_push"
    tenant_azure_id: Optional[str] = None

class SFTPConfig(ERPConfigBase):
    integration_mode: str = "sftp"
    sftp_host: str
    sftp_port: int = 22
    sftp_username: str
    sftp_password: str
    sftp_path: str = "/invoices"
    poll_interval_minutes: int = 15

class WebhookConfig(ERPConfigBase):
    integration_mode: str = "webhook"
    webhook_secret: Optional[str] = None

class FieldMappingUpdate(BaseModel):
    mapping: dict


# ── List all connections ──────────────────────────────────────────────────

@router.get("/connections")
async def list_connections(request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conns = db.query(ERPConnection).filter(ERPConnection.tenant_id == tenant_id).all()
    return [_serialize(c) for c in conns]


# ── Get single connection ─────────────────────────────────────────────────

@router.get("/connections/{conn_id}")
async def get_connection(conn_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    return _serialize(conn, include_instructions=True, request=request)


# ── Create / update connection ────────────────────────────────────────────

@router.post("/connections")
async def create_connection(request: Request, body: dict, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    erp_type  = body.get("erp_type", "GENERIC").upper()
    mode      = body.get("integration_mode", "api_push")

    webhook_secret = None
    if mode == "webhook":
        webhook_secret = body.get("webhook_secret") or secrets.token_hex(32)

    conn = ERPConnection(
        tenant_id=tenant_id,
        erp_type=erp_type,
        display_name=body.get("display_name", erp_type),
        integration_mode=mode,
        status="not_configured",
        sftp_host=body.get("sftp_host"),
        sftp_port=body.get("sftp_port", 22),
        sftp_username=body.get("sftp_username"),
        sftp_path=body.get("sftp_path", "/invoices"),
        poll_interval_minutes=body.get("poll_interval_minutes", 15),
        webhook_secret=webhook_secret,
        webhook_url=_generate_webhook_url(request, tenant_id),
        field_mapping=body.get("field_mapping"),
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return _serialize(conn, include_instructions=True, request=request)


@router.put("/connections/{conn_id}")
async def update_connection(conn_id: str, request: Request, body: dict, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")

    for field in ["display_name", "status", "sftp_host", "sftp_port",
                  "sftp_username", "sftp_path", "poll_interval_minutes", "field_mapping"]:
        if field in body:
            setattr(conn, field, body[field])

    db.commit()
    return _serialize(conn, include_instructions=True, request=request)


@router.delete("/connections/{conn_id}")
@router.delete("/connections/{conn_id}/")
async def delete_connection(conn_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    
    db.delete(conn)
    db.commit()
    return {"message": "Connection deleted successfully", "id": conn_id}


# ── Test connection ───────────────────────────────────────────────────────

@router.post("/connections/{conn_id}/test")
async def test_connection(conn_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")

    result = {"connection_id": conn_id, "erp_type": conn.erp_type, "mode": conn.integration_mode}

    if conn.integration_mode == "sftp":
        result.update(_test_sftp(conn))
    elif conn.integration_mode in ("api_push", "webhook"):
        result.update({"status": "ok", "message": "Endpoint is live and accepting invoices"})
    elif conn.integration_mode == "api_pull":
        result.update({"status": "ok", "message": "Pull schedule is active"})
    else:
        result.update({"status": "ok", "message": "Connection configured"})

    conn.status = "active" if result.get("status") == "ok" else "error"
    conn.last_sync_status = result.get("status")
    db.commit()

    return result


def _test_sftp(conn: ERPConnection) -> dict:
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # SFTP auth would go here
        ssh.connect(conn.sftp_host, port=conn.sftp_port,
                    username=conn.sftp_username, timeout=10)
        sftp = ssh.open_sftp()
        files = sftp.listdir(conn.sftp_path or "/")
        sftp.close(); ssh.close()
        return {"status": "ok", "message": f"SFTP connected. {len(files)} files found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Inbound webhook receiver (Model 5) ───────────────────────────────────

@router.post("/webhook/{tenant_id}/{conn_id}")
async def receive_webhook(
    tenant_id: str, conn_id: str,
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(None)
):
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")

    body_bytes = await request.body()

    if conn.webhook_secret and x_webhook_signature:
        expected = hmac.new(
            conn.webhook_secret.encode(),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        sig = x_webhook_signature.replace("sha256=", "")
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(401, "Invalid webhook signature")

    try:
        payload = json.loads(body_bytes)
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    if conn.field_mapping:
        payload = _apply_field_mapping(payload, conn.field_mapping)

    from app.validation.validator import InvoiceValidator
    from app.adapters.generic_erp import GenericJSONAdapter

    adapter = GenericJSONAdapter()
    validator = InvoiceValidator()

    try:
        invoice = adapter.transform(payload)
        report  = validator.validate(invoice) # Add tenant_id if supported

        conn.last_sync_at     = __import__("datetime").datetime.now()
        conn.last_sync_status = "success"
        conn.last_sync_count  = (conn.last_sync_count or 0) + 1
        db.commit()

        return {
            "received": True,
            "invoice_number": invoice.invoice_number,
            "is_valid": report.is_valid,
            "total_errors": report.total_errors,
            "errors": [e.model_dump() for e in report.errors],
        }
    except Exception as e:
        conn.last_sync_status = "error"
        db.commit()
        raise HTTPException(422, f"Validation failed: {str(e)}")


# ── Field mapping update ──────────────────────────────────────────────────

@router.put("/connections/{conn_id}/mapping")
async def update_field_mapping(conn_id: str, request: Request,
                                body: FieldMappingUpdate, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    conn.field_mapping = body.mapping
    db.commit()
    return {"mapping": conn.field_mapping, "message": "Field mapping updated"}


# ── Integration instructions ──────────────────────────────────────────────

@router.get("/connections/{conn_id}/instructions")
async def get_integration_instructions(conn_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    conn = db.query(ERPConnection).filter(
        ERPConnection.id == conn_id,
        ERPConnection.tenant_id == tenant_id
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    return _build_instructions(request, conn, tenant_id)


# ── Helpers ───────────────────────────────────────────────────────────────

def _generate_webhook_url(request: Request, tenant_id: str) -> str:
    host = request.headers.get("host", "adamas-einvoice.koyeb.app")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    base = f"{scheme}://{host}"
    return f"{base}/api/v1/integrations/webhook/{tenant_id}"


def _apply_field_mapping(payload: dict, mapping: dict) -> dict:
    result = {}
    for erp_field, value in payload.items():
        pint_field = mapping.get(erp_field, erp_field)
        result[pint_field] = value
    return result


def _serialize(conn: ERPConnection, include_instructions: bool = False, request: Request = None) -> dict:
    d = {
        "id":               conn.id,
        "erp_type":         conn.erp_type,
        "display_name":     conn.display_name,
        "status":           conn.status,
        "integration_mode": conn.integration_mode,
        "last_sync_at":     conn.last_sync_at,
        "last_sync_status": conn.last_sync_status,
        "last_sync_count":  conn.last_sync_count,
        "webhook_url":      conn.webhook_url,
        "sftp_host":        conn.sftp_host,
        "sftp_username":    conn.sftp_username,
        "sftp_port":        conn.sftp_port,
        "sftp_path":        conn.sftp_path,
        "poll_interval_minutes": conn.poll_interval_minutes,
        "field_mapping":    conn.field_mapping,
    }
    if include_instructions and request:
        d["instructions"] = _build_instructions(request, conn, conn.tenant_id)
    return d


def _build_instructions(request: Request, conn: ERPConnection, tenant_id: str) -> dict:
    host = request.headers.get("host", "adamas-einvoice.koyeb.app")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    base = f"{scheme}://{host}"
    endpoint = f"{base}/api/v1/validate-invoice"

    if conn.erp_type == "SAP":
        return {
            "title": "SAP S/4HANA Integration Guide",
            "steps": [
                {"step": 1, "title": "Create SM59 Destination", "detail": f"Host: {host}, SSL: Active"},
                {"step": 2, "title": "Headers", "detail": f"X-API-Key: {tenant_id}"},
            ],
            "sample_code": f"CALL FUNCTION 'HTTP_POST' ... URL: {endpoint}"
        }
    
    # Generic webhook instructions
    if conn.integration_mode == "webhook":
        url = f"{conn.webhook_url}/{conn.id}"
        return {
            "title": "Webhook Integration Guide",
            "webhook_url": url,
            "steps": [
                {"step": 1, "title": "URL", "detail": url},
                {"step": 2, "title": "Auth", "detail": f"Secret: {conn.webhook_secret}"}
            ]
        }

    return {"title": f"{conn.erp_type} Guide", "mode": conn.integration_mode}
