from fastapi import APIRouter, Depends, Query, Request, HTTPException
import os

from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.db.session import get_db
from app.db.models import ClientSubmission, SubmissionValidationError
from app.services.storage_service import storage_service
from fastapi.responses import Response
import json

router = APIRouter()

@router.get("/submissions")
async def get_audit_submissions(
    request: Request,
    db: Session = Depends(get_db),
    client_id: str = Query(..., description="Client ID for multi-tenant filtering"),
    status: str = Query(None, description="Filter by Accepted/Rejected"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    skip: int = 0,
    limit: int = 50
):
    """Enterprise Stage 1: Professional ASP Integration Portal for handshake logs."""
    query = db.query(ClientSubmission).filter(ClientSubmission.client_id == client_id)
    
    if status:
        query = query.filter(ClientSubmission.overall_status == status)

    if start_date:
        query = query.filter(ClientSubmission.submission_timestamp >= start_date)
    if end_date:
        # Append 23:59:59 to end date to include the whole day
        query = query.filter(ClientSubmission.submission_timestamp <= f"{end_date} 23:59:59")
        
    total = query.count()
    items = query.order_by(desc(ClientSubmission.submission_timestamp)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "submission_id": item.submission_id,
                "invoice_number": item.invoice_number,
                "status": item.overall_status,
                "http_status": item.http_status_code,
                "timestamp": item.submission_timestamp.isoformat(),
                "response_path": item.raw_response_path,
                "request_path": item.raw_request_path,
                "source_filename": item.source_filename,
                "source_module": item.source_module,
                "error_count": db.query(SubmissionValidationError).filter(SubmissionValidationError.submission_id == item.submission_id).count()
            }
            for item in items
        ]
    }

@router.get("/raw-payload")
async def get_raw_response_payload(
    client_id: str,
    submission_id: str,
    doc_type: str = Query("request", regex="^(request|response)$"),
    db: Session = Depends(get_db)
):
    """Retrieve the auditable raw payload (XML or JSON) using DB lookup."""
    submission = db.query(ClientSubmission).filter(
        ClientSubmission.submission_id == submission_id,
        ClientSubmission.client_id == client_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Audit record not found.")

    path = submission.raw_request_path if doc_type == "request" else submission.raw_response_path
    
    if not path or not os.path.exists(path):
        # Fallback to response if request is missing for older records
        if doc_type == "request" and submission.raw_response_path and os.path.exists(submission.raw_response_path):
            path = submission.raw_response_path
            doc_type = "response"
        else:
            raise HTTPException(status_code=404, detail=f"File not found on disk.")
            
    # Enforce correct media type and extension based on doc_type and path
    if doc_type == "request":
        media_type = "application/xml"
        ext = "xml"
    else:
        # Responses might be JSON or XML (if it's a signed XML)
        if path.endswith(".xml"):
            media_type = "application/xml"
            ext = "xml"
        else:
            media_type = "application/json"
            ext = "json"
    
    with open(path, "rb") as f:
        content = f.read()
        
    filename = f"ASP_{doc_type.upper()}_{submission_id[:8]}.{ext}"
    
    return Response(
        content=content, 
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Type",
            "X-File-Name": filename
        }
    )
    
    # For S3 or as fallback
    # ... logic for S3 payload retrieval ...
    
    raise HTTPException(status_code=404, detail=f"File not found at {path}")
