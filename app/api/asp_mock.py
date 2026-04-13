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
    ASP Mock Validation endpoint integrated with Peppol.
    """
    from app.adapters.xml_builder import generate_ubl_xml
    from app.validation.peppol_api import validate_with_peppol_api
    
    xml_str = generate_ubl_xml(payload)
    peppol_res = await validate_with_peppol_api(xml_str)
    
    if peppol_res.get("status") == "valid":
        return {
            "status": "ACCEPTED", # for UI mapped status
            "asp_status": "ACCEPTED",
            "message": "Invoice passed Peppol Compliance and is accepted for FTA submission",
            "invoice_number": payload.invoice_number,
            "timestamp": utc_now(),
            "asp_reference": f"ASP-{uuid4().hex[:8].upper()}",
            "peppol_result": peppol_res
        }
    else:
        errors = [f"[{e.get('rule')}] {e.get('message')}" for e in peppol_res.get('errors', [])]
        return {
            "status": "REJECTED",
            "asp_status": "REJECTED",
            "message": "Failed strictly enforced Peppol Validation Rules",
            "invoice_number": payload.invoice_number,
            "timestamp": utc_now(),
            "errors": errors,
            "peppol_result": peppol_res
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
