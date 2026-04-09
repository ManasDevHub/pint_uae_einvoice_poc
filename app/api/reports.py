from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.db.models import ValidationRun
import datetime
import io
import csv
from collections import defaultdict

router = APIRouter()

def _get_date_range(period: str):
    """Return (start_date, label) for given period."""
    now = datetime.datetime.utcnow()
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = now.strftime("%d %b %Y")
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = now.strftime("%B %Y")
    elif period == "quarterly":
        q_month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=q_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        q = (now.month - 1) // 3 + 1
        label = f"Q{q} {now.year}"
    elif period == "yearly":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        label = str(now.year)
    else:
        start = None
        label = "All Time"
    return start, label

@router.get("/reports")
async def get_report(
    request: Request,
    db: Session = Depends(get_db),
    period: str = Query("monthly", description="daily | monthly | quarterly | yearly | all")
):
    """Generate a comprehensive date-filtered report of validation activity."""
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    start, label = _get_date_range(period)

    query = db.query(ValidationRun).filter(ValidationRun.tenant_id == tenant_id)
    if start:
        query = query.filter(ValidationRun.created_at >= start)

    runs = query.order_by(desc(ValidationRun.created_at)).all()

    total = len(runs)
    valid_count = sum(1 for r in runs if r.is_valid)
    failed_count = total - valid_count
    pass_rate = round((valid_count / total * 100) if total > 0 else 0, 1)

    category_counts = defaultdict(int)
    field_errors = defaultdict(int)
    rule_messages = {}

    for run in runs:
        if run.errors_json and isinstance(run.errors_json, list):
            for err in run.errors_json:
                cat = err.get("category", "COMPLIANCE")
                field = err.get("field", "Unknown")
                msg = err.get("error") or err.get("message", "")
                category_counts[cat] += 1
                field_errors[field] += 1
                if field not in rule_messages:
                    rule_messages[field] = msg

    by_category = [{"name": k, "value": v} for k, v in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]
    top_failing_rules = [
        {
            "field": k,
            "count": v,
            "message": rule_messages.get(k, ""),
            "fail_rate": round(v / total * 100, 1) if total > 0 else 0
        }
        for k, v in sorted(field_errors.items(), key=lambda x: x[1], reverse=True)[:15]
    ]

    date_breakdown = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
    for run in runs:
        run_date = run.created_at.strftime("%Y-%m-%d") if run.created_at else "unknown"
        date_breakdown[run_date]["total"] += 1
        if run.is_valid:
            date_breakdown[run_date]["passed"] += 1
        else:
            date_breakdown[run_date]["failed"] += 1

    daily_breakdown = [
        {"date": d, **stats}
        for d, stats in sorted(date_breakdown.items())
    ]

    return {
        "period": period,
        "period_label": label,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "summary": {
            "total_invoices": total,
            "valid": valid_count,
            "failed": failed_count,
            "pass_rate": pass_rate
        },
        "by_category": by_category,
        "top_failing_rules": top_failing_rules,
        "daily_breakdown": daily_breakdown
    }

@router.get("/reports/export")
async def export_report(
    request: Request,
    db: Session = Depends(get_db),
    period: str = Query("monthly", description="daily | monthly | quarterly | yearly | all")
):
    """Export a comprehensive date-filtered report as CSV."""
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    start, label = _get_date_range(period)

    query = db.query(ValidationRun).filter(ValidationRun.tenant_id == tenant_id)
    if start:
        query = query.filter(ValidationRun.created_at >= start)
    runs = query.order_by(desc(ValidationRun.created_at)).all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([f"UAE PINT AE E-Invoice Compliance Report — {label}"])
        writer.writerow([f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"])
        writer.writerow([])

        total = len(runs)
        valid = sum(1 for r in runs if r.is_valid)
        writer.writerow(["SUMMARY"])
        writer.writerow(["Total Invoices", total])
        writer.writerow(["Valid", valid])
        writer.writerow(["Failed", total - valid])
        writer.writerow(["Pass Rate", f"{round(valid/total*100, 1) if total else 0}%"])
        writer.writerow([])
        yield output.getvalue()
        output.truncate(0); output.seek(0)

        writer.writerow(["INVOICE DETAIL"])
        writer.writerow(["Invoice Number", "Date", "Type", "Status", "Pass %", "Errors", "Timestamp"])
        yield output.getvalue()
        output.truncate(0); output.seek(0)

        for run in runs:
            writer.writerow([
                run.invoice_number,
                run.invoice_date,
                run.invoice_type_code,
                "VALID" if run.is_valid else "INVALID",
                run.pass_percentage,
                run.total_errors,
                run.created_at
            ])
            yield output.getvalue()
            output.truncate(0); output.seek(0)

    filename = f"uae_pint_ae_report_{period}_{datetime.datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
