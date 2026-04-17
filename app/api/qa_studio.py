from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import TestRun
from app.services.storage_service import storage_service
from app.tests.test_runner import enterpriseTestRunner
from datetime import datetime
import uuid
import os

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload-repository")
async def upload_test_repo(
    client_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """SaaS Phase 2: Upload Excel repository to S3/Local."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files accepted")
    
    # Save to storage
    content = await file.read()
    storage_path = storage_service.upload_file(
        "test_cases", 
        file.filename, 
        content, 
        client_id
    )
    
    return {
        "status": "SUCCESS",
        "filename": file.filename,
        "storage_path": storage_path,
        "client_id": client_id
    }

@router.post("/trigger-run")
async def trigger_test_run(
    client_id: str,
    background_tasks: BackgroundTasks,
    run_type: str = "full",
    limit: int = 558,
    include_pint: bool = True,
    include_business: bool = True,
    db: Session = Depends(get_db)
):
    """SaaS Phase 2: Trigger async test run with segmented rules."""
    # 1. Initialize Runner
    runner = enterpriseTestRunner()
    
    # 2. Add to background tasks
    background_tasks.add_task(
        runner.run_suite, 
        client_id=client_id, 
        run_type=run_type, 
        limit=limit,
        include_pint=include_pint,
        include_business=include_business
    )
    
    return {
        "status": "PENDING",
        "message": f"QA Sandbox started: {'PINT' if include_pint else ''} {'& Business' if include_business else ''} rules selected.",
        "estimated_completion": f"{limit * 0.1} seconds"
    }

@router.get("/status")
async def get_qa_status(client_id: str, db: Session = Depends(get_db)):
    """Live feed for the frontend Command Center."""
    runs = db.query(TestRun).filter(TestRun.client_id == client_id).order_by(TestRun.created_at.desc()).limit(5).all()
    return runs
