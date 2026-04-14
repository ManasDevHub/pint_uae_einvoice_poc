# app/etl/tasks/transform.py

from app.etl.celery_app import celery_app
from app.adapters.generic_erp import GenericJSONAdapter
from app.db.session import SessionLocal
from app.db.models import ETLJob, ETLRowError, ETLJobStatus
import logging
import pydantic

log = logging.getLogger(__name__)
adapter = GenericJSONAdapter()

CHUNK_SIZE = 50   # process 50 rows per Celery task — keeps memory low


@celery_app.task(name="app.etl.tasks.transform.transform_batch", max_retries=3)
def transform_batch(job_id: str, raw_rows: list, tenant_id: str = "anonymous", full_pipeline: bool = False):
    """
    Stage 2: Transform — adapter normalises raw rows to InvoicePayload.
    Splits into chunks and fans out to validate tasks.
    """
    db = SessionLocal()
    try:
        valid_invoices = []
        row_errors = []

        for i, row in enumerate(raw_rows):
            try:
                invoice = adapter.transform(row)
                valid_invoices.append((i + 1, invoice, row))
            except pydantic.ValidationError as e:
                row_errors.append(ETLRowError(
                    etl_job_id=job_id,
                    row_number=i + 1,
                    invoice_number=row.get("invoice_number", "Unknown"),
                    error_type="SCHEMA",
                    error_message=str(e),
                    raw_data=row,
                ))
            except Exception as e:
                row_errors.append(ETLRowError(
                    etl_job_id=job_id,
                    row_number=i + 1,
                    invoice_number=row.get("invoice_number", "Unknown"),
                    error_type="PARSE",
                    error_message=str(e),
                    raw_data=row,
                ))

        if row_errors:
            db.bulk_save_objects(row_errors)
            job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
            if job:
                job.failed_rows = len(row_errors)
            db.commit()

        log.info(f"ETL Transform: job={job_id}, valid={len(valid_invoices)}, errors={len(row_errors)}")

        # Fan out validation in chunks
        chunks = [valid_invoices[i:i+CHUNK_SIZE] for i in range(0, len(valid_invoices), CHUNK_SIZE)]
        from app.etl.tasks.validate import validate_chunk

        for chunk_idx, chunk in enumerate(chunks):
            # Serialize invoice objects to dict for Celery (can't pass Pydantic objects)
            # FIX: Ensure 'serialized' is clearly defined and use model_dump()
            serialized_data = []
            for r_num, inv, raw in chunk:
                serialized_data.append((r_num, inv.model_dump(), raw))
            
            try:
                validate_chunk(job_id, chunk_idx, serialized_data, len(raw_rows), len(row_errors), tenant_id=tenant_id, full_pipeline=full_pipeline)
            except Exception as e:
                log.error(f"ETL Validation Stage failed: {e}")
                # Fallback to direct call is already forced here

        if not valid_invoices:
            # All rows failed transform — mark job done
            from app.db.session import SessionLocal as SL
            db2 = SL()
            try:
                job = db2.query(ETLJob).filter(ETLJob.id == job_id).first()
                if job:
                    job.status = ETLJobStatus.PARTIAL.value
                    job.failed_rows = len(row_errors)
                    db2.commit()
            finally:
                db2.close()

        return {"job_id": job_id, "transformed": len(valid_invoices), "failed": len(row_errors)}

    except Exception as exc:
        log.error(f"ETL Transform failed: job={job_id}, error={exc}")
        # Mark job as failed in DB
        from app.db.session import SessionLocal as SL
        db2 = SL()
        try:
            job = db2.query(ETLJob).filter(ETLJob.id == job_id).first()
            if job:
                from datetime import datetime, timezone
                job.status = ETLJobStatus.FAILED.value
                job.error_message = f"Transform phase failed: {str(exc)}"
                job.completed_at = datetime.now(timezone.utc)
                db2.commit()
                log.info(f"Updated job {job_id} status to FAILED")
        except Exception as e:
            log.error(f"Failed to update job status to FAILED: {e}")
        finally:
            db2.close()

        from celery import current_task
        if current_task:
            raise current_task.retry(exc=exc, countdown=5)
        raise exc
    finally:
        db.close()
