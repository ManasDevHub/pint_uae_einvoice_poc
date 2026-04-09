from fastapi import APIRouter, Header, HTTPException
from app.models.invoice import InvoicePayload
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

router = APIRouter()

def utc_now():
    return datetime.now(timezone.utc).isoformat()

@router.post("/validate")
async def mock_asp_validate(
    payload: InvoicePayload,
    x_pre_validated: Optional[str] = Header(None),  # optional bypass header
):
    """
    ASP Mock Validation endpoint.
    
    IMPORTANT: This endpoint trusts that /api/v1/validate-invoice has already 
    been called and passed. It does NOT re-run independent validation.
    The frontend pipeline enforces the correct order:
      validate → asp/validate → asp/submit
    """
    return {
        "asp_status": "ACCEPTED",
        "message": "Invoice accepted for FTA submission",
        "invoice_number": payload.invoice_number,
        "timestamp": utc_now(),
        "asp_reference": f"ASP-{uuid4().hex[:8].upper()}",
    }

@router.post("/submit")
async def mock_asp_submit(payload: InvoicePayload):
    """
    FTA Mock Submission endpoint.
    
    Issues a simulated clearance ID.
    Only reachable from the frontend if ASP validation passed.
    """
    clearance_id   = f"CLR-{uuid4().hex[:10].upper()}"
    fta_reference  = f"FTA-AE-{uuid4().hex[:8].upper()}"

    return {
        "asp_status": "CLEARED",
        "clearance_id": clearance_id,
        "invoice_number": payload.invoice_number,
        "timestamp": utc_now(),
        "fta_reference": fta_reference,
        "peppol_endpoint": f"urn:oasis:names:tc:ebcore:partyid-type:unregistered:C4:{fta_reference}",
    }
