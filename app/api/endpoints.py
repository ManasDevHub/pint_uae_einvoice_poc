from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
import hashlib
import json
import time
import re
import pydantic
from sqlalchemy.orm import Session
from app.models.report import APIResponse
from app.validation.validator import InvoiceValidator
from app.adapters.generic_erp import GenericJSONAdapter
from app.db.session import get_db
from app.db.models import ValidationRun
from app.core.config import settings

from app.core.logging import log
from prometheus_client import Counter, Histogram
INVOICES_VALIDATED = Counter("invoices_validated_total", "Total invoices", ["tenant_id", "transaction_type", "result"])
VALIDATION_DURATION = Histogram("validation_duration_seconds", "Validation duration")
VALIDATION_ERRORS = Counter("validation_errors_total", "Errors by category", ["category", "error_code"])

import redis
try:
    # Use short timeouts to prevent the app from hanging if Redis is offline
    redis_client = redis.Redis.from_url(
        settings.redis_url, 
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1
    )
    redis_client.ping()
except Exception:
    redis_client = None

router = APIRouter()
validator = InvoiceValidator()

def get_adapter():
    return GenericJSONAdapter()

def invoice_fingerprint(payload: dict) -> str:
    key = f"{payload.get('invoice_number')}:{payload.get('invoice_date')}:{payload.get('seller', {}).get('seller_trn')}"
    return hashlib.sha256(key.encode()).hexdigest()

from slowapi.util import get_remote_address
from slowapi import Limiter
def get_tenant_key(request: Request):
    return getattr(request.state, "tenant_id", get_remote_address(request))
limiter = Limiter(key_func=get_tenant_key)

@router.post("/validate-invoice", response_model=APIResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def validate_invoice(request: Request, raw_payload: Dict[str, Any], db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    
    # 1. Duplicate check (Rule 8)
    fingerprint = invoice_fingerprint(raw_payload)
    no_cache = request.query_params.get("nocache", "false").lower() == "true"
    
    if redis_client and not no_cache:
        cached = redis_client.get(f"invoice:{fingerprint}")
        if cached:
            log.info(f"Cache hit for invoice {fingerprint}")
            return json.loads(cached)

    try:
        adapter = get_adapter()
        # Log absolute path of rules for production debugging
        from app.validation.validator import DEFAULT_RULES_PATH
        log.info(f"Validating invoice {raw_payload.get('invoice_number')} using rules at {DEFAULT_RULES_PATH}")
        # Input Sanitization (Rule 20)
        def sanitize_string(value: Any) -> Any:
            if not isinstance(value, str): return value
            return re.sub(r'[\x00-\x1f\x7f]', '', value)[:100]
            
        if "invoice_number" in raw_payload:
            raw_payload["invoice_number"] = sanitize_string(raw_payload["invoice_number"])
            
        invoice = adapter.transform(raw_payload)
        
        with VALIDATION_DURATION.time():
            report = validator.validate(invoice)
            
        if report.is_valid:
            status = "SUCCESS"
            message = "Invoice is valid according to UAE PINT AE rules."
        else:
            status = "FAILURE"
            message = f"Found {report.total_errors} validation errors."
            
        response_data = APIResponse(
            status=status,
            message=message,
            report=report
        )
        
        # 2. Redis Metrics (Rule 5)
        INVOICES_VALIDATED.labels(
            tenant_id=tenant_id,
            transaction_type=invoice.transaction_type,
            result="valid" if report.is_valid else "invalid"
        ).inc()
        for error in report.errors:
            VALIDATION_ERRORS.labels(category=error.category, error_code=error.field).inc()
            
        # 3. Cache Duplicate (Rule 8)
        if redis_client:
            redis_client.setex(f"invoice:{fingerprint}", settings.duplicate_cache_ttl, response_data.model_dump_json())
            
        # 4. Persistence DB Audit Log (Rule 7)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        try:
            log.info(f"Persisting validation result for {report.invoice_number}")
            run = ValidationRun(
                tenant_id=tenant_id,
                invoice_number=report.invoice_number,
                invoice_date=invoice.invoice_date,
                transaction_type=invoice.transaction_type,
                invoice_type_code=invoice.invoice_type_code,
                is_valid=report.is_valid,
                total_errors=report.total_errors,
                pass_percentage=report.metrics.pass_percentage,
                errors_json=[e.model_dump() for e in report.errors],
                raw_payload=raw_payload,
                duration_ms=elapsed_ms
            )
            db.add(run)
            db.commit()
            log.info(f"Audit log committed for {report.invoice_number}")
        except Exception as db_err:
            db.rollback()
            log.error(f"Failed to commit audit log for {report.invoice_number}: {db_err}")
            # We do NOT raise an error here because the validation result itself is valid
            # and MUST be returned to the user for the demo.
        
        return response_data
    except pydantic.ValidationError as e:
        from app.validation.helpers import build_report_from_error
        log.warning(f"Schema validation failed for payload: {str(e)}")
        report = build_report_from_error(e, invoice_number=raw_payload.get("invoice_number", "Unknown"))
        
        return APIResponse(
            status="FAILURE",
            message="Payload does not match UAE PINT AE schema requirements.",
            report=report
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        log.error(f"Critical error in validate_invoice: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Validation Error: {str(e)}")
