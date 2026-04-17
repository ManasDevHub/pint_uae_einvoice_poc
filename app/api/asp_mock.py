from fastapi import APIRouter, Header, HTTPException, Depends, Query, Request
from app.models.invoice import InvoicePayload
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.asp_mock import ASPMockService

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
async def mock_asp_submit(
    payload: InvoicePayload,
    client_id: str = Query("demo-client-phase2"),
    source_filename: Optional[str] = Query(None),
    source_module: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    FTA Mock Submission endpoint with persistent logging.
    """
    from app.adapters.xml_builder import generate_ubl_xml
    
    service = ASPMockService(db)
    xml_str = generate_ubl_xml(payload)
    
    res = service.submit_invoice(
        client_id=client_id,
        xml_data=xml_str,
        invoice_number=payload.invoice_number,
        source_filename=source_filename,
        source_module=source_module
    )
    
    return {
        "asp_status": "CLEARED",
        "clearance_id": res.get("submissionId"),
        "invoice_number": payload.invoice_number,
        "timestamp": res.get("timestamp"),
        "fta_reference": f"FTA-AE-{uuid4().hex[:8].upper()}",
        "submission_details": res
    }

@router.post("/batch-submit")
async def mock_asp_batch_submit(
    payloads: List[InvoicePayload],
    client_id: str = Query("demo-client-phase2"),
    source_filename: Optional[str] = Query(None),
    source_module: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Bulk submission to ASP with persistent audit logging.
    """
    from app.adapters.xml_builder import generate_ubl_xml
    service = ASPMockService(db)
    
    results = []
    for p in payloads:
        xml_str = generate_ubl_xml(p)
        res = service.submit_invoice(
            client_id=client_id,
            xml_data=xml_str,
            invoice_number=p.invoice_number,
            source_filename=source_filename,
            source_module=source_module
        )
        results.append({
            "invoice_number": p.invoice_number,
            "clearance_id": res.get("submissionId"),
            "status": res.get("status")
        })
        
    return {
        "status": "COMPLETE",
        "batch_size": len(payloads),
        "results": results,
        "timestamp": utc_now()
    }

@router.post("/submit-validated")
async def mock_asp_submit_validated(
    request: Request,
    invoice_numbers: List[str],
    source_module: str,
    source_filename: Optional[str] = None,
    client_id: str = Query("demo-client-phase2"),
    db: Session = Depends(get_db)
):
    """
    Submits already validated invoices to ASP by fetching their stored raw payloads.
    """
    from app.db.models import ValidationRun
    from app.adapters.generic_erp import GenericJSONAdapter
    from app.adapters.xml_builder import generate_ubl_xml
    from app.services.asp_mock import ASPMockService
    
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    service = ASPMockService(db)
    adapter = GenericJSONAdapter()
    
    # 1. Fetch the runs
    runs = db.query(ValidationRun).filter(
        ValidationRun.invoice_number.in_(invoice_numbers),
        ValidationRun.tenant_id == tenant_id,
        ValidationRun.is_valid == True
    ).all()
    
    if not runs:
        raise HTTPException(status_code=404, detail="No valid validation runs found for these invoice numbers.")
    
    results = []
    for run in runs:
        try:
            # 2. Transform the stored raw_payload back into an Invoice object
            # Note: raw_payload is already a dict in the DB
            invoice = adapter.transform(run.raw_payload)
            
            # 3. Generate XML
            xml_str = generate_ubl_xml(invoice)
            
            # 4. Submit to ASP Simulation
            res = service.submit_invoice(
                client_id=client_id,
                xml_data=xml_str,
                invoice_number=run.invoice_number,
                source_filename=source_filename,
                source_module=source_module
            )
            
            results.append({
                "invoice_number": run.invoice_number,
                "status": "Submitted",
                "clearance_id": res.get("submissionId"),
                "asp_status": res.get("status")
            })
        except Exception as e:
            results.append({
                "invoice_number": run.invoice_number,
                "status": "Failed",
                "error": str(e)
            })
            
    return {
        "status": "COMPLETE",
        "total": len(invoice_numbers),
        "submitted": len([r for r in results if r["status"] == "Submitted"]),
        "results": results
    }
