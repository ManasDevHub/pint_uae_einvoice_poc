# app/etl/tasks/load.py

from app.etl.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import ETLJob, ETLJobStatus, ValidationRun
from datetime import datetime, timezone
from uuid import uuid4
import logging

log = logging.getLogger(__name__)


def _update_redis_status(batch_id: str, status: str, total: int, done: int):
    """Sync job status to Redis for backward-compatible UI polling."""
    from app.core.config import settings
    import redis
    import json
    try:
        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        data = {"status": status, "total": total, "done": done, "batch_id": batch_id}
        r.setex(f"batch:{batch_id}", 3600, json.dumps(data))
    except Exception as e:
        log.warning(f"Failed to update Redis for job {batch_id}: {e}")


@celery_app.task(name="app.etl.tasks.load.load_chunk", max_retries=3)
def load_chunk(job_id: str, chunk_idx: int, results: list,
               total_rows: int, pre_failed: int, tenant_id: str):
    """
    Stage 4: Load — bulk insert validated results into PostgreSQL.
    Updates ETL job progress atomically.
    """
    db = SessionLocal()
    try:
        # Bulk insert ValidationRun records
        run_objects = [
            ValidationRun(
                id=str(uuid4()),
                tenant_id=tenant_id,
                invoice_number=r["invoice_number"],
                invoice_date=r.get("invoice_date"),
                transaction_type=r.get("transaction_type"),
                invoice_type_code=r.get("invoice_type_code"),
                seller_trn=r.get("seller_trn"),
                buyer_trn=r.get("buyer_trn"),
                seller_name=r.get("seller_name"),
                buyer_name=r.get("buyer_name"),
                currency_code=r.get("currency_code"),
                tax_category_code=r.get("tax_category_code"),
                total_with_tax=r.get("total_with_tax"),
                is_valid=r["is_valid"],
                total_errors=r["total_errors"],
                total_checks=r.get("total_checks", 0),
                pass_percentage=r.get("pass_percentage"),
                errors_json=r.get("errors_json"),
                field_results_json=r.get("field_results_json"),
                raw_payload=r.get("raw_payload"),
                duration_ms=r.get("duration_ms"),
                source=r.get("source", "etl"),
                etl_job_id=job_id,
            )
            for r in results
        ]
        log.info(f"ETL Load Stage: Attempting to save {len(run_objects)} validation runs for job {job_id}")
        db.bulk_save_objects(run_objects)
        db.commit() # Commit insertions first to ensure data state
        log.info(f"ETL Load Stage: Successfully committed {len(run_objects)} records for job {job_id}")

        # Update job counters atomically
        from sqlalchemy import update
        valid_in_chunk   = sum(1 for r in results if r["is_valid"])
        invalid_in_chunk = sum(1 for r in results if not r["is_valid"])

        # Atomic update for processed rows
        db.query(ETLJob).filter(ETLJob.id == job_id).update({
            "processed_rows": ETLJob.processed_rows + len(results),
            "valid_rows":      ETLJob.valid_rows + valid_in_chunk,
            "invalid_rows":    ETLJob.invalid_rows + invalid_in_chunk
        }, synchronize_session=False)
        db.commit()

        # Check if all rows are done
        job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
        if job:
            total_processed = job.processed_rows + job.failed_rows
            if total_processed >= job.total_rows:
                job.status       = ETLJobStatus.COMPLETE.value if job.failed_rows == 0 else ETLJobStatus.PARTIAL.value
                job.completed_at = datetime.now(timezone.utc)
                if job.started_at:
                    # Handle SQLite potential naive datetimes
                    s_at = job.started_at
                    if s_at.tzinfo is None:
                        s_at = s_at.replace(tzinfo=timezone.utc)
                    delta = (job.completed_at - s_at).total_seconds() * 1000
                    job.duration_ms = round(delta, 2)
                
                # Sync to Redis for UI
                _update_redis_status(job.batch_id, job.status, job.total_rows, job.processed_rows)
                
                log.info(f"ETL Job SUCCESS: job={job_id}, total_rows={job.total_rows}, duration={job.duration_ms}ms")
            else:
                # Still processing - update Redis with progress
                _update_redis_status(job.batch_id, "PROCESSING", job.total_rows, job.processed_rows)

        db.commit()
        log.info(f"ETL Load chunk {chunk_idx}: job={job_id}, inserted={len(run_objects)} records to PostgreSQL")

        return {"job_id": job_id, "chunk": chunk_idx, "loaded": len(run_objects)}

    except Exception as exc:
        db.rollback()
        log.error(f"ETL Load failed: job={job_id}, error={exc}")
        
        # Mark job as failed in DB
        from app.db.session import SessionLocal as SL
        db2 = SL()
        try:
            job = db2.query(ETLJob).filter(ETLJob.id == job_id).first()
            if job:
                job.status = ETLJobStatus.FAILED.value
                job.error_message = f"Load phase failed at chunk {chunk_idx}: {str(exc)}"
                job.completed_at = datetime.now(timezone.utc)
                db2.commit()
                log.info(f"Updated job {job_id} status to FAILED in load")
        except Exception as e:
            log.error(f"Failed to update job status to FAILED in load: {e}")
        finally:
            db2.close()

        from celery import current_task
        if current_task:
            raise current_task.retry(exc=exc, countdown=5)
        raise exc
    finally:
        db.close()
