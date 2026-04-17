# app/etl/tasks/extract.py

from app.etl.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import ETLJob, ETLJobStatus
from datetime import datetime, timezone
import pandas as pd
import io
import logging

log = logging.getLogger(__name__)


def _update_job(db, job_id: str, **kwargs):
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
        db.commit()


STRING_FIELDS = {
    "invoice_type_code", "payment_means_type_code", "currency_code",
    "tax_category_code", "transaction_type", "seller_country_code",
    "buyer_country_code", "unit_of_measure", "tax_category",
    "seller_trn", "buyer_trn", "line_id", "seller_subdivision",
    "buyer_subdivision", "seller_registration_identifier_type",
    "buyer_registration_identifier_type",
}


def coerce_row(row: dict) -> dict:
    """Force string fields to str, handle NaN, strip whitespace, and zero-pad TRNs."""
    import math
    cleaned = {}
    for k, v in row.items():
        if isinstance(v, float) and math.isnan(v):
            cleaned[k] = ""
            continue
        
        val_str = str(v).strip()
        if val_str.lower() == "nan":
            val_str = ""

        # Handle Scientific notation or .0 from Excel
        if ".0" in val_str and val_str.endswith(".0"):
            try:
                val_str = str(int(float(val_str)))
            except: pass

        if k in STRING_FIELDS:
            # Special handling for TRNs: zero-pad to 15 digits
            if k in ["seller_trn", "buyer_trn"] and val_str.isdigit():
                val_str = val_str.zfill(15)
            cleaned[k] = val_str
        else:
            cleaned[k] = v
    return cleaned


def group_invoices(records: list) -> list:
    """Group flat rows by invoice_number to support multi-line invoices."""
    grouped = {}
    for r in records:
        inv_no = str(r.get("invoice_number", "")).strip()
        if not inv_no:
            continue
            
        if inv_no not in grouped:
            # First time seeing this invoice, initialize with header data
            grouped[inv_no] = r.copy()
            grouped[inv_no]["lines"] = []
            
        # Add line data
        LINE_KEYS = {
            "line_id", "item_name", "item_description", "unit_of_measure",
            "quantity", "unit_price", "gross_price", "price_base_quantity",
            "discount_amount", "line_net_amount", "tax_category", "tax_rate",
            "tax_amount", "aed_tax_amount"
        }
        line_data = {k: v for k, v in r.items() if k in LINE_KEYS or k.startswith("line_")}
        grouped[inv_no]["lines"].append(line_data)
        
    return list(grouped.values())


@celery_app.task(name="app.etl.tasks.extract.extract_excel", max_retries=3)
def extract_excel(job_id: str, file_bytes_hex: str, filename: str, tenant_id: str = "anonymous", full_pipeline: bool = False):
    """
    Stage 1: Extract — parse Excel/CSV bytes into a list of row dicts.
    Returns list of grouped invoices to be picked up by transform task.
    """
    db = SessionLocal()
    try:
        _update_job(db, job_id,
                    status=ETLJobStatus.RUNNING.value,
                    started_at=datetime.now(timezone.utc))

        file_bytes = bytes.fromhex(file_bytes_hex)
        buf = io.BytesIO(file_bytes)

        if filename.endswith(".csv"):
            # Excel often saves CSV with UTF-8-BOM (utf-8-sig)
            df = pd.read_csv(buf, dtype=str, encoding='utf-8-sig')
        else:
            df = pd.read_excel(buf, dtype=str)

        df = df.fillna("")
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        
        # 1. Validate mandatory columns
        mandatory = ["invoice_number", "invoice_date", "seller_trn", "buyer_name"]
        missing = [m for m in mandatory if m not in df.columns]
        if missing:
            raise ValueError(f"Wrong format data. Missing required columns: {', '.join(missing)}")

        raw_records = df.to_dict("records")
        # 1. Clean data (coercion, TRN padding)
        cleaned_records = [coerce_row(r) for r in raw_records]
        
        # 2. Group by invoice_number
        grouped_records = group_invoices(cleaned_records)

        _update_job(db, job_id, total_rows=len(grouped_records))
        log.info(f"ETL Extract complete: job={job_id}, invoices={len(grouped_records)}, total_rows={len(cleaned_records)}")

        # Chain to transform with direct synchronous call
        try:
            from app.etl.tasks.transform import transform_batch
            transform_batch(job_id, grouped_records, tenant_id=tenant_id, full_pipeline=full_pipeline)
        except Exception as e:
            log.error(f"ETL Transform Stage failed: {e}")
            raise e

        return {"job_id": job_id, "invoices_extracted": len(grouped_records)}

    except Exception as exc:
        try:
            _update_job(db, job_id,
                        status=ETLJobStatus.FAILED.value,
                        error_message=str(exc),
                        completed_at=datetime.now(timezone.utc))
            log.info(f"Updated job {job_id} status to FAILED due to extraction error")
        except Exception as e:
            log.error(f"Failed to update job status to FAILED in extract: {e}")
        
        log.error(f"ETL Extract failed: job={job_id}, error={exc}")
        from celery import current_task
        # Do not retry on configuration/format errors (ValueError)
        if current_task and not isinstance(exc, ValueError):
            raise current_task.retry(exc=exc, countdown=5)
        raise exc
    finally:
        db.close()
