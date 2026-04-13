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
    """Force string fields to str, handle NaN, strip whitespace."""
    import math
    cleaned = {}
    for k, v in row.items():
        if isinstance(v, float) and math.isnan(v):
            cleaned[k] = None
            continue
        if k in STRING_FIELDS:
            cleaned[k] = str(int(v)) if isinstance(v, float) and v == int(v) else str(v)
        else:
            cleaned[k] = v
    return cleaned


@celery_app.task(name="app.etl.tasks.extract.extract_excel", max_retries=3)
def extract_excel(job_id: str, file_bytes_hex: str, filename: str, tenant_id: str = "anonymous"):
    """
    Stage 1: Extract — parse Excel/CSV bytes into a list of row dicts.
    Returns list of raw row dicts to be picked up by transform task.
    """
    db = SessionLocal()
    try:
        _update_job(db, job_id,
                    status=ETLJobStatus.RUNNING.value,
                    started_at=datetime.now(timezone.utc))

        file_bytes = bytes.fromhex(file_bytes_hex)
        buf = io.BytesIO(file_bytes)

        if filename.endswith(".csv"):
            df = pd.read_csv(buf, dtype=str)
        else:
            df = pd.read_excel(buf, dtype=str)

        df = df.fillna("")
        df.columns = [str(c).strip() for c in df.columns]
        records = df.to_dict("records")
        records = [r for r in records if any(str(v).strip() for v in r.values())]
        records = [coerce_row(r) for r in records]

        _update_job(db, job_id, total_rows=len(records))
        log.info(f"ETL Extract complete: job={job_id}, rows={len(records)}")

        # Chain to transform with direct synchronous call
        try:
            from app.etl.tasks.transform import transform_batch
            transform_batch(job_id, records, tenant_id=tenant_id)
        except Exception as e:
            log.error(f"ETL Transform Stage failed: {e}")
            raise e

        return {"job_id": job_id, "rows_extracted": len(records)}

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
        if current_task:
            raise current_task.retry(exc=exc, countdown=5)
        raise exc
    finally:
        db.close()
