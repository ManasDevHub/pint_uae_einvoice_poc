import json
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import structlog

log = structlog.get_logger()

async def json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=400,
        content={
            "status": "FAILURE",
            "message": "Malformed JSON payload",
            "report": {
                "invoice_number": "N/A",
                "is_valid": False,
                "total_errors": 1,
                "errors": [{
                    "field": "JSON Structure",
                    "error": f"Syntax Error: {exc.msg} at line {exc.lineno}, col {exc.colno}",
                    "severity": "HIGH",
                    "category": "FORMAT"
                }],
                "warnings": [],
                "metrics": {
                    "total_checks": 1, "passed_checks": 0, "failed_checks": 1, "pass_percentage": 0.0
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "field_results": []
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(l) for l in e["loc"]),
         "error": e["msg"],
         "severity": "HIGH",
         "category": "FORMAT"}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "status": "FAILURE",
            "message": "Request schema validation failed",
            "report": {
                "invoice_number": "N/A",
                "is_valid": False,
                "total_errors": len(errors),
                "errors": errors,
                "warnings": [],
                "metrics": {
                    "total_checks": len(errors),
                    "passed_checks": 0,
                    "failed_checks": len(errors),
                    "pass_percentage": 0.0
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "field_results": [] # Placeholder to prevent UI crash
            }
        }
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "ERROR", "message": "Internal server error",
                 "request_id": request.headers.get("X-Request-ID")}
    )
