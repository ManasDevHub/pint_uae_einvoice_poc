from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import structlog

log = structlog.get_logger()

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "FAILURE",
            "message": "Request schema validation failed",
            "report": {
                "invoice_number": None,
                "is_valid": False,
                "total_errors": len(exc.errors()),
                "errors": [
                    {"field": ".".join(str(l) for l in e["loc"]),
                     "error": e["msg"],
                     "severity": "HIGH",
                     "category": "FORMAT"}
                    for e in exc.errors()
                ],
                "warnings": [],
                "metrics": {
                    "total_checks": len(exc.errors()),
                    "passed_checks": 0,
                    "failed_checks": len(exc.errors()),
                    "pass_percentage": 0.0
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
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
