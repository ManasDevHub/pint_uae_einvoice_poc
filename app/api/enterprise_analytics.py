from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from app.db.session import SessionLocal
from app.db.models import ClientSubmission, SubmissionFieldMetric, TestRun, SubmissionValidationError
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/executive")
async def get_enterprise_executive(
    client_id: str = Query(..., description="Client ID for multi-tenant isolation"),
    days: int = Query(30, description="Range in days"),
    db: Session = Depends(get_db)
):
    """SECTION 5.1: High-level tiles for acceptance, rejection, and volume."""
    since = datetime.now() - timedelta(days=days)
    
    total = db.query(func.count(ClientSubmission.submission_id)).filter(
        ClientSubmission.client_id == client_id,
        ClientSubmission.submission_timestamp >= since
    ).scalar() or 0
    
    accepted = db.query(func.count(ClientSubmission.submission_id)).filter(
        ClientSubmission.client_id == client_id,
        ClientSubmission.overall_status == "Accepted",
        ClientSubmission.submission_timestamp >= since
    ).scalar() or 0
    
    rejected = db.query(func.count(ClientSubmission.submission_id)).filter(
        ClientSubmission.client_id == client_id,
        ClientSubmission.overall_status == "Rejected",
        ClientSubmission.submission_timestamp >= since
    ).scalar() or 0

    return {
        "summary": {
            "total_invoices": total,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": round((accepted / total * 100), 2) if total > 0 else 0,
            "target_benchmark": 98.0
        }
    }

@router.get("/heatmap")
async def get_compliance_heatmap(
    client_id: str = Query(..., description="Client ID"),
    db: Session = Depends(get_db)
):
    """SECTION 5.3: 51-field compliance heatmap generator."""
    # Group by field_name and calculate validity rate
    metrics = db.query(
        SubmissionFieldMetric.field_name,
        func.count(SubmissionFieldMetric.id).label("total"),
        func.sum(case((SubmissionFieldMetric.is_valid == True, 1), else_=0)).label("valid_count")
    ).filter(
        SubmissionFieldMetric.client_id == client_id
    ).group_by(SubmissionFieldMetric.field_name).all()

    heatmap = []
    for m in metrics:
        total = m.total or 0
        valid = m.valid_count or 0
        heatmap.append({
            "field": m.field_name,
            "compliance_rate": round((valid / total * 100), 2) if total > 0 else 0,
            "total_checks": total
        })

    return heatmap

@router.get("/test-history")
async def get_test_run_history(
    client_id: str = Query(..., description="Client ID"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """SECTION 3: PASS/FAIL trends for QA test batches."""
    runs = db.query(TestRun).filter(
        TestRun.client_id == client_id
    ).order_by(desc(TestRun.start_time)).limit(limit).all()

    return [{
        "run_id": r.id,
        "run_type": r.run_type,
        "pass_rate": r.pass_rate,
        "passed": r.passed,
        "failed": r.failed,
        "timestamp": r.start_time.isoformat()
    } for r in runs]
