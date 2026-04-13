# app/etl/tasks/validate.py

from app.etl.celery_app import celery_app
from app.validation.validator import InvoiceValidator
from app.models.invoice import InvoicePayload
from app.db.session import SessionLocal
from app.db.models import ETLJob, ETLJobStatus, ETLRowError
from datetime import datetime, timezone
import logging
import time

log = logging.getLogger(__name__)
validator = InvoiceValidator()


@celery_app.task(name="app.etl.tasks.validate.validate_chunk", max_retries=3)
def validate_chunk(job_id: str, chunk_idx: int, serialized_invoices: list,
                   total_rows: int, pre_failed: int, tenant_id: str = "anonymous"):
    """
    Stage 3: Validate — run all 51 PINT AE rules on each invoice in chunk.
    Passes validated results to load task.
    """
    db = SessionLocal()
    try:
        results = []
        tenant_id = None

        for row_num, invoice_dict, raw_payload in serialized_invoices:
            invoice = InvoicePayload(**invoice_dict)

            t0 = time.perf_counter()
            report = validator.validate(invoice)
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)

            results.append({
                "row_number":        row_num,
                "invoice_number":    invoice.invoice_number,
                "invoice_date":      invoice.invoice_date,
                "transaction_type":  invoice.transaction_type,
                "invoice_type_code": invoice.invoice_type_code,
                "seller_trn":        invoice.seller.trn if invoice.seller else None,
                "buyer_trn":         invoice.buyer.trn if invoice.buyer else None,
                "seller_name":       invoice.seller.name if invoice.seller else None,
                "buyer_name":        invoice.buyer.name if invoice.buyer else None,
                "currency_code":     invoice.currency_code,
                "tax_category_code": invoice.tax_category_code,
                "total_with_tax":    invoice.totals.total_with_tax if invoice.totals else None,
                "is_valid":          report.is_valid,
                "total_errors":      report.total_errors,
                "total_checks":      report.metrics.total_checks,
                "pass_percentage":   report.metrics.pass_percentage,
                "errors_json":       [e.model_dump() for e in report.errors],
                "field_results_json":[g.model_dump() for g in report.field_results],
                "raw_payload":       raw_payload,
                "duration_ms":       duration_ms,
                "source":            "etl",
                "job_id":            job_id,
            })

        log.info(f"ETL Validate chunk {chunk_idx}: job={job_id}, validated={len(results)}")

        from app.etl.tasks.load import load_chunk
        load_chunk(job_id, chunk_idx, results, total_rows, pre_failed, tenant_id)

        return {"job_id": job_id, "chunk": chunk_idx, "validated": len(results)}

    except Exception as exc:
        log.error(f"ETL Validate chunk {chunk_idx} failed: job={job_id}, error={exc}")
        
        # Mark job as failed in DB
        from app.db.session import SessionLocal as SL
        db2 = SL()
        try:
            from app.db.models import ETLJob, ETLJobStatus
            job = db2.query(ETLJob).filter(ETLJob.id == job_id).first()
            if job:
                from datetime import datetime, timezone
                job.status = ETLJobStatus.FAILED.value
                job.error_message = f"Validation phase failed at chunk {chunk_idx}: {str(exc)}"
                job.completed_at = datetime.now(timezone.utc)
                db2.commit()
                log.info(f"Updated job {job_id} status to FAILED in validate")
        except Exception as e:
            log.error(f"Failed to update job status to FAILED in validate: {e}")
        finally:
            db2.close()

        from celery import current_task
        if current_task:
            raise current_task.retry(exc=exc, countdown=5)
        raise exc
    finally:
        db.close()
