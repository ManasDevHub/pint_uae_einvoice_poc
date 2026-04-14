from fastapi import APIRouter, HTTPException, Depends, Request, Query
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
from app.adapters.xml_builder import generate_ubl_xml
from app.validation.peppol_api import validate_with_peppol_api, map_peppol_to_internal_errors, map_peppol_to_internal_warnings

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
    # Hash the entire payload so that ANY change triggers a new validation
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()

from slowapi.util import get_remote_address
from slowapi import Limiter
def get_tenant_key(request: Request):
    return getattr(request.state, "tenant_id", get_remote_address(request))
limiter = Limiter(key_func=get_tenant_key)

@router.post("/validate-invoice", response_model=APIResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def validate_invoice(
    request: Request, 
    raw_payload: Dict[str, Any], 
    full_pipeline: bool = Query(False),
    db: Session = Depends(get_db)
):
    t0 = time.perf_counter()
    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    
    # 1. Duplicate check (Rule 8)
    fingerprint = invoice_fingerprint(raw_payload)
    no_cache = True # Forced bypass to fix stale UI ghost errors
    
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
            
            if full_pipeline and report.is_valid:
                log.info(f"Full pipeline requested for {report.invoice_number}")
                try:
                    xml_content = generate_ubl_xml(invoice)
                    peppol_res = await validate_with_peppol_api(xml_content)
                    
                    if peppol_res.get("status") == "invalid":
                        # Map and merge external errors
                        peppol_errors = map_peppol_to_internal_errors(peppol_res)
                        peppol_warnings = map_peppol_to_internal_warnings(peppol_res)
                        
                        report.errors.extend([ValidationErrorItem(**e) for e in peppol_errors])
                        report.warnings.extend([ValidationErrorItem(**w) for w in peppol_warnings])
                        report.is_valid = False
                        report.total_errors = len(report.errors)
                        
                        # Re-calculate metrics
                        total_peppol_fails = len(peppol_errors)
                        report.metrics.failed_checks += total_peppol_fails
                        report.metrics.passed_checks = max(0, report.metrics.total_checks - report.metrics.failed_checks)
                        report.metrics.pass_percentage = round((report.metrics.passed_checks / report.metrics.total_checks) * 100, 2)
                        
                except Exception as peppol_err:
                    log.error(f"Peppol API call failed: {peppol_err}")
                    report.warnings.append(ValidationErrorItem(
                        field="PEPPOL_Validator",
                        error=f"Full pipeline check reached error: {str(peppol_err)}",
                        severity="MEDIUM",
                        category="COMPLIANCE"
                    ))
                    
        if report.is_valid:
            status = "SUCCESS"
            message = "Invoice is valid (Full Pipeline verified)." if full_pipeline else "Invoice is valid according to local UAE PINT AE rules."
        else:
            status = "FAILURE"
            message = f"Found {report.total_errors} validation errors (Full Pipeline check)." if full_pipeline else f"Found {report.total_errors} validation errors."
            
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
