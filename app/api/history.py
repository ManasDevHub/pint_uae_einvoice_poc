from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.db.session import get_db
from app.db.models import ValidationRun
from fastapi.responses import StreamingResponse
import io
import csv
import datetime

router = APIRouter()

@router.get("/history")
async def get_history(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_valid: Optional[bool] = None,
    invoice_type_code: Optional[str] = None,
    search: Optional[str] = None,
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$")
):
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    query = db.query(ValidationRun).filter(ValidationRun.tenant_id == tenant_id)
    
    if start_date and end_date:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(ValidationRun.created_at >= start, ValidationRun.created_at <= end)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                ValidationRun.invoice_number.ilike(search_filter),
                ValidationRun.transaction_type.ilike(search_filter)
            )
        )
        
    if is_valid is not None:
        query = query.filter(ValidationRun.is_valid == is_valid)
    if invoice_type_code is not None:
        query = query.filter(ValidationRun.invoice_type_code == invoice_type_code)
        
    total = query.count()
    runs = query.order_by(desc(ValidationRun.created_at)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": run.id,
                "invoice_number": run.invoice_number,
                "invoice_date": run.invoice_date,
                "transaction_type": run.transaction_type,
                "invoice_type_code": run.invoice_type_code,
                "is_valid": run.is_valid,
                "total_errors": run.total_errors,
                "pass_percentage": run.pass_percentage,
                "created_at": run.created_at
            }
            for run in runs
        ]
    }

@router.get("/history/{run_id}")
async def get_history_detail(run_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    run = db.query(ValidationRun).filter(
        ValidationRun.id == run_id,
        ValidationRun.tenant_id == tenant_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "invoice_number": run.invoice_number,
        "is_valid": run.is_valid,
        "errors": run.errors_json,
        "raw_payload": run.raw_payload,
        "created_at": run.created_at,
        "pass_percentage": run.pass_percentage
    }

@router.get("/export/csv")
async def export_csv(
    request: Request,
    db: Session = Depends(get_db),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$")
):
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    query = db.query(ValidationRun).filter(ValidationRun.tenant_id == tenant_id)
    
    if start_date and end_date:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(ValidationRun.created_at >= start, ValidationRun.created_at <= end)
        
    runs = query.order_by(desc(ValidationRun.created_at)).limit(1000).all()
    
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Invoice Number", "Date", "Transaction Type", "Type Code", "Status", "Pass %", "Total Errors", "Timestamp"
        ])
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
        
        for run in runs:
            writer.writerow([
                run.id,
                run.invoice_number,
                run.invoice_date,
                run.transaction_type,
                run.invoice_type_code,
                "VALID" if run.is_valid else "INVALID",
                run.pass_percentage,
                run.total_errors,
                run.created_at
            ])
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)
            
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=validation_history.csv",
            "Cache-Control": "no-cache"
        }
    )
