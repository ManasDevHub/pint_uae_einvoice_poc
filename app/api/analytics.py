from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.session import get_db
from app.db.models import ValidationRun
import datetime
import traceback
import io
import csv
import json
import os
from collections import defaultdict

router = APIRouter()

# Load all 51 PINT AE rules at startup
_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "rules", "uae_pint_ae_rules.json")
try:
    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        _ALL_RULES = json.load(f).get("fields", [])
except Exception:
    _ALL_RULES = []

# Additional cross-field / hardcoded rules not in the JSON
_HARDCODED_RULES = [
    {"field": "unit_price", "message": "A6.5: Net price must equal Gross price minus Discount/Qty", "category": "CALCULATION", "rules": ["cross_field_calc"]},
    {"field": "quantity", "message": "E11: Negative quantities not allowed for Standard Invoice", "category": "CALCULATION", "rules": ["negative_qty_check"]},
    {"field": "invoiced_item_tax_category", "message": "E10: Line tax category must match header tax category", "category": "COMPLIANCE", "rules": ["tax_category_consistency"]},
    {"field": "unit_of_measure", "message": "A6.3: Unit of Measure must be valid UN/ECE Rec 20", "category": "COMPLIANCE", "rules": ["valid_uom"]},
    {"field": "tax_amount", "message": "A6.9: Line tax must match line_net_amount × tax_rate", "category": "CALCULATION", "rules": ["line_tax_calc"]},
    {"field": "tax_rate", "message": "A5.4: Standard Category (S) must be 5%; Z/E/O must be 0%", "category": "COMPLIANCE", "rules": ["vat_rate_enforcement"]},
    {"field": "line_extension_amount", "message": "A4.1: Sum of line net amounts must equal line_extension_amount", "category": "CALCULATION", "rules": ["sum_lines_check"]},
    {"field": "total_without_tax", "message": "A4.2: Total without tax must equal sum of lines", "category": "CALCULATION", "rules": ["total_without_tax_calc"]},
    {"field": "tax_amount", "message": "A4.3: Total tax must equal sum of line taxes", "category": "CALCULATION", "rules": ["total_tax_calc"]},
    {"field": "total_with_tax", "message": "A4.4: total_without_tax + tax_amount must equal total_with_tax", "category": "CALCULATION", "rules": ["grand_total_calc"]},
    {"field": "tax_amount", "message": "A4.5: Exempt/Zero-rated category must have zero total tax", "category": "CALCULATION", "rules": ["zero_tax_category"]},
    {"field": "tax_subtotals", "message": "A5: Tax Breakdown is mandatory", "category": "COMPLIANCE", "rules": ["tax_breakdown_required"]},
    {"field": "tax_subtotals.tax_amount", "message": "A5.2: Tax breakdown tax amount must match rate", "category": "CALCULATION", "rules": ["tax_subtotal_calc"]},
]

ALL_RULES = _ALL_RULES + _HARDCODED_RULES

def _get_date_range(period: str, start_date: str = None, end_date: str = None):
    """Return (start_date, end_date) for given period or custom."""
    now = datetime.datetime.utcnow()
    end = None
    if start_date and end_date:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    elif period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "quarterly":
        q_month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=q_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "yearly":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = None
    return start, (end or now)

async def get_analytics_summary(
    request: Request,
    db: Session = Depends(get_db),
    period: str = Query("all", description="all | daily | monthly | quarterly | yearly | custom"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$")
):
    try:
        tenant_id = getattr(request.state, "tenant_id", "anonymous")
        query = db.query(ValidationRun).filter(ValidationRun.tenant_id == tenant_id)
        start, end = _get_date_range(period, start_date, end_date)
        if start:
            query = query.filter(ValidationRun.created_at >= start)
        if end and start_date and end_date:
            query = query.filter(ValidationRun.created_at <= end)

        runs = query.all()

        total = len(runs)
        valid_count = sum(1 for r in runs if r.is_valid)
        failed_count = total - valid_count
        pass_rate = (valid_count / total * 100) if total > 0 else 0

        category_counts = defaultdict(int)
        field_errors = defaultdict(int)

        for run in runs:
            if run.errors_json and isinstance(run.errors_json, list):
                for err in run.errors_json:
                    cat = err.get("category", "COMPLIANCE")
                    field = err.get("field", "Unknown Field")
                    category_counts[cat] += 1
                    field_errors[field] += 1

        by_category = [{"name": k, "value": v} for k, v in category_counts.items()]
        top_errors = [{"field": k, "count": v} for k, v in sorted(field_errors.items(), key=lambda x: x[1], reverse=True)[:10]]

        today = datetime.datetime.utcnow().date()
        date_counts = defaultdict(lambda: {"total": 0, "passed": 0})

        for run in runs:
            run_date = run.created_at.date() if run.created_at else today
            date_counts[run_date]["total"] += 1
            if run.is_valid:
                date_counts[run_date]["passed"] += 1

        trend = []
        for i in range(6, -1, -1):
            target_date = today - datetime.timedelta(days=i)
            day_stats = date_counts[target_date]
            daily_pass_rate = (day_stats["passed"] / day_stats["total"] * 100) if day_stats["total"] > 0 else 0
            trend.append({"date": target_date.strftime("%a"), "pass_rate": round(daily_pass_rate, 1)})

        latest_runs = [
            {
                "id": r.id,
                "invoice_number": r.invoice_number,
                "is_valid": r.is_valid,
                "created_at": r.created_at,
                "pass_percentage": r.pass_percentage
            }
            for r in sorted(runs, key=lambda x: x.created_at, reverse=True)[:5]
        ]

        return {
            "total": total,
            "pass_rate": round(pass_rate, 1),
            "failures": failed_count,
            "by_category": by_category,
            "trend": trend,
            "top_errors": top_errors,
            "latest_runs": latest_runs,
            "period": period
        }
    except Exception as e:
        traceback.print_exc()
        return {"total": 0, "pass_rate": 0, "failures": 0, "by_category": [], "trend": [], "top_errors": [], "period": period}

@router.get("/analytics/rules")
async def get_all_rules_with_stats(
    request: Request,
    db: Session = Depends(get_db),
    period: str = Query("all", description="all | daily | monthly | quarterly | yearly | custom"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$")
):
    """Return all 51+ PINT AE rules with live pass/fail counts from the database."""
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    query = db.query(ValidationRun).filter(ValidationRun.tenant_id == tenant_id)
    start, end = _get_date_range(period, start_date, end_date)
    if start:
        query = query.filter(ValidationRun.created_at >= start)
    if end and start_date and end_date:
        query = query.filter(ValidationRun.created_at <= end)
    runs = query.all()

    total_runs = len(runs)
    field_fail_counts = defaultdict(int)
    for run in runs:
        if run.errors_json and isinstance(run.errors_json, list):
            failed_fields = set()
            for err in run.errors_json:
                field = err.get("field", "")
                if field:
                    field_fail_counts[field] += 1
                    failed_fields.add(field)

    result = []
    seen_fields = set()
    for rule in ALL_RULES:
        field = rule["field"]
        key = f"{field}:{rule.get('message', '')}"
        if key in seen_fields:
            continue
        seen_fields.add(key)

        fail_count = field_fail_counts.get(field, 0)
        pass_count = total_runs - fail_count if total_runs > 0 else 0

        result.append({
            "field": field,
            "message": rule.get("message", ""),
            "category": rule.get("category", "COMPLIANCE"),
            "rules": rule.get("rules", []),
            "total_checked": total_runs,
            "passed": max(0, pass_count),
            "failed": fail_count,
            "pass_rate": round((pass_count / total_runs * 100) if total_runs > 0 else 100, 1)
        })

    return {
        "total_rules": len(result),
        "total_invoices_checked": total_runs,
        "period": period,
        "rules": result
    }

@router.get("/analytics/failures/{field_name}")
async def get_field_failures(field_name: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    runs = db.query(ValidationRun).filter(
        ValidationRun.is_valid == False,
        ValidationRun.tenant_id == tenant_id
    ).order_by(desc(ValidationRun.created_at)).limit(100).all()

    details = []
    for run in runs:
        if run.errors_json:
            for err in run.errors_json:
                if err.get("field") == field_name:
                    details.append({
                        "id": run.id,
                        "invoice_number": run.invoice_number,
                        "timestamp": run.created_at,
                        "message": err.get("error") or err.get("message"),
                        "category": err.get("category"),
                        "severity": err.get("severity", "HIGH")
                    })
                    break

    return {"field": field_name, "count": len(details), "items": details}

@router.get("/analytics/failures/{field_name}/export")
async def export_field_failures(field_name: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    runs = db.query(ValidationRun).filter(
        ValidationRun.is_valid == False,
        ValidationRun.tenant_id == tenant_id
    ).order_by(desc(ValidationRun.created_at)).all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Invoice Number", "Date", "Error Message", "Category", "Severity", "Field"])
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
        for run in runs:
            if run.errors_json:
                for err in run.errors_json:
                    if err.get("field") == field_name:
                        writer.writerow([
                            run.invoice_number,
                            run.created_at,
                            err.get("error") or err.get("message"),
                            err.get("category"),
                            err.get("severity", "HIGH"),
                            field_name
                        ])
                        yield output.getvalue()
                        output.truncate(0)
                        output.seek(0)

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=failures_{field_name}.csv"}
    )
