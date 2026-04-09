import structlog
import logging
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            tenant_id=getattr(request.state, "tenant_id", "anonymous"),
            path=request.url.path,
            method=request.method,
        )
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            log.info("request_complete", status=response.status_code, duration_ms=elapsed)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            log.error("request_failed", error=str(e), duration_ms=elapsed, exc_info=True)
            raise
