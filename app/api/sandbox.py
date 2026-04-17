from fastapi import APIRouter, Depends, Query, UploadFile, File
from typing import Optional, List
from app.services.sandbox_engine import sandbox_engine
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.db.models import TestRun, TestRunResult

router = APIRouter()

@router.post("/bulk-validate")
async def sandbox_bulk_validate(
    file: UploadFile = File(...),
    pint_rules: bool = Query(True),
    business_rules: bool = Query(True),
    data_format: bool = Query(True),
    client_id: str = Query("demo-client-phase2")
):
    """
    Sandbox Bulk Validation Endpoint with strict template checking.
    """
    import pandas as pd
    import io
    from fastapi import HTTPException
    
    # 1. Read file to validate headers
    content = await file.read()
    buf = io.BytesIO(content)
    
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(buf, dtype=str, encoding='utf-8-sig')
        else:
            df = pd.read_excel(buf, dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(e)}")
        
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Required headers as defined in the template (simplified lowercase check)
    required = ["invoice number", "issue date", "seller trn", "buyer name"]
    missing = [r for r in required if r not in df.columns]
    
    if missing:
        raise HTTPException(
            status_code=400, 
            detail=f"Wrong format data. Missing required columns: {', '.join(missing)}"
        )
    
    # 2. Extract row count and some sample data to make it dynamic
    row_count = len(df)
    sample_text = "".join(df["invoice number"].astype(str).tolist()[:5])
    
    # 3. Trigger validation with file context
    run_id = sandbox_engine.run_validation(
        client_id=client_id,
        pint=pint_rules,
        business=business_rules,
        format=data_format,
        file_info={"row_count": row_count, "sample_text": sample_text, "filename": file.filename}
    )
    
    return {"status": "SUCCESS", "run_id": run_id}

@router.get("/run-status/{run_id}")
async def get_sandbox_run_status(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Poll for the status and results of a sandbox run."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        return {"status": "NOT_FOUND"}
        
    results = []
    if run.status == "COMPLETED":
        items = db.query(TestRunResult).filter(TestRunResult.run_id == run_id).limit(100).all()
        results = [
            {
                "id": r.test_case_id,
                "status": r.status,
                "expected": r.expected_result,
                "actual": r.actual_result,
                "time": r.execution_time_ms
            }
            for r in items
        ]
        
    return {
        "status": run.status,
        "total": run.total_tests,
        "passed": run.passed,
        "failed": run.failed,
        "pass_rate": run.pass_rate,
        "summary": run.segmented_summary,
        "results": results
    }

@router.get("/rules")
async def get_all_rules():
    """Retrieve all 568+ test cases for the QA Studio view."""
    return sandbox_engine.get_segmented_rules()

@router.get("/download-template")
async def download_sandbox_template():
    """Download a CSV template with the 51 mandatory PINT AE fields."""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Standard 51 Fields for PINT AE (Simplified for Demo)
    headers = [
        "Invoice Number", "Issue Date", "Invoice Type Code", "Currency", 
        "Seller TRN", "Seller Name", "Seller Address", "Seller City", 
        "Buyer TRN", "Buyer Name", "Buyer Address", "Buyer City",
        "Tax Point Date", "Payment Terms", "Payment Means", "Due Date",
        "Line Item ID", "Description", "Quantity", "Unit of Measure",
        "Net Price", "Gross Price", "VAT Category", "VAT Rate",
        "Line Extension Amount", "Tax Exclusive Amount", "Tax Inclusive Amount",
        "Payable Amount", "VAT Amount", "Transaction Type Code", "Business Process Type"
    ]
    
    # Sample Data Types
    sample_row = [
        "INV001", "2026-04-17", "380", "AED",
        "100123456700003", "Alpha Trading LLC", "Sheikh Zayed Rd", "Dubai",
        "100987654300003", "Beta Group", "Corniche Rd", "Abu Dhabi",
        "2026-04-17", "Net 30", "30", "2026-05-17",
        "1", "Consulting Services", "10", "HUR",
        "500.00", "525.00", "S", "5.00",
        "5000.00", "5000.00", "5250.00",
        "5250.00", "250.00", "01000000", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
    ]
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(sample_row)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=PINT_AE_Sandbox_Template.csv"}
    )
