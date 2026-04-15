from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from app.api.endpoints import router as validate_router
from app.api.asp_mock import router as mock_router
from app.api.health import router as health_router
from app.api.batch import router as batch_router
from app.api.history import router as history_router
from app.api.analytics import router as analytics_router
from app.api.auth_router import router as auth_router
from app.api.reports import router as reports_router
from app.api.integrations import router as integrations_router
from app.api.api_keys import router as system_api_keys_router
from app.core.config import settings
from app.core.logging import RequestLoggingMiddleware, log
from app.core.exceptions import validation_exception_handler, unhandled_exception_handler
from app.db.session import init_db
import hashlib
import secrets

# Init DB
init_db()

app = FastAPI(
    title=settings.app_name,
    description="""## Enterprise E-Invoicing Validation Engine Aligned with **UAE PINT AE** mandatory field requirements.
### Endpoints
- **`/api/v1/validate-invoice`** — Accepts raw ERP payloads (SAP, Oracle, Dynamics).
  Adapter normalises to PINT AE schema before validation.
- **`/asp/v1/validate`** — Accepts pre-normalised PINT AE payload. Simulates ASP forwarding.
- **`/asp/v1/submit`** — Simulates FTA submission. Returns clearance ID.
- **`/api/v1/batch-validate`** — Submit up to 500 invoices asynchronously.
### Error Categories
| Category | Description |
|---|---|
| `FORMAT` | Field format or presence violation |
| `CALCULATION` | Mathematical inconsistency |
| `COMPLIANCE` | PINT AE business rule violation |
    """,
    version=settings.api_version,
    contact={"name": "E-Invoicing POC", "email": "support@yourdomain.com"},
    license_info={"name": "Proprietary"}
)

# SlowAPI Limiter setup
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
def get_tenant_key(request: Request):
    return getattr(request.state, "tenant_id", get_remote_address(request))
limiter = Limiter(key_func=get_tenant_key)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middlewares (Order matters: outermost first)
@app.middleware("http")
async def limit_payload_size(request: Request, call_next):
    if request.headers.get("content-length"):
        if int(request.headers.get("content-length")) > settings.max_payload_bytes:
            return JSONResponse(status_code=413, content={"error": "Payload too large"})
    return await call_next(request)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "connect-src 'self' http://localhost:8000;"
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://52.66.111.65:8000",
        "http://52.66.111.65"
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
    allow_credentials=True,
)
app.add_middleware(RequestLoggingMiddleware)

# --- Integrated Auth Middleware ---
VALID_KEYS = {
    hashlib.sha256(k.encode()).hexdigest(): k
    for k in settings.api_keys.split(",") if k
}

@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    path = request.url.path
    
    # Exempt routes that use JWT/Session auth or are public
    exempt_prefixes = {"/assets", "/docs", "/openapi.json", "/health", "/metrics", "/auth", "/api/v1/system"}
    exempt_exact = {"/", "/favicon.svg", "/icons.svg"}

    if path in exempt_exact or any(path.startswith(p) for p in exempt_prefixes):
        return await call_next(request)
        
    # Standard Web UI uses 'Authorization: Bearer <token>'
    # If this header is present, we allow the request to pass to the router-level auth
    if request.headers.get("Authorization"):
        return await call_next(request)

    # Only enforce X-API-Key for actual integration endpoints
    if not (path.startswith("/api") or path.startswith("/asp")):
        return await call_next(request)

    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not key:
        return JSONResponse(
            status_code=401, 
            content={"status": "FAILURE", "message": "X-API-Key header required for integration access"}
        )
    
    hashed = hashlib.sha256(key.encode()).hexdigest()
    tenant_id = VALID_KEYS.get(hashed)

    if not tenant_id:
        # Check DB for dynamic keys
        from app.db.session import SessionLocal
        from app.db.models import SystemApiKey
        db = SessionLocal()
        try:
            db_key = db.query(SystemApiKey).filter(
                SystemApiKey.hashed_key == hashed,
                SystemApiKey.is_active == True
            ).first()
            if db_key:
                tenant_id = db_key.tenant_id
                # Update last used
                db_key.last_used_at = __import__("datetime").datetime.now()
                db.commit()
        finally:
            db.close()

    if not tenant_id:
        return JSONResponse(status_code=403, content={"status": "FAILURE", "message": "Invalid API key"})
        
    request.state.tenant_id = tenant_id
    return await call_next(request)

# Exceptions
import json
from app.core.exceptions import json_decode_exception_handler
app.add_exception_handler(json.JSONDecodeError, json_decode_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Prometheus setup
from prometheus_client import make_asgi_app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Routers
app.include_router(health_router, prefix="/health", tags=["Health Probes"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(batch_router, prefix="/api/v1", tags=["Batch Processing"])
app.include_router(validate_router, prefix="/api/v1", tags=["Internal Validation"])
app.include_router(history_router, prefix="/api/v1", tags=["History API"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics API"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports API"])
app.include_router(mock_router, prefix="/asp/v1", tags=["ASP Mock Simulation"])
app.include_router(integrations_router, prefix="/api/v1/integrations", tags=["ERP Integrations"])
app.include_router(system_api_keys_router, prefix="/api/v1/system", tags=["System API Keys"])

# ── Serve React build ──
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

# Serve static assets (JS, CSS, images)
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

# SPA Fallback: Serve index.html for 404s on non-API routes
# This fixes React Router (reload on /validate, /history etc works)
# and prevents interference with /docs, /openapi.json etc.
@app.exception_handler(404)
async def spa_fallback_handler(request: Request, exc):
    path = request.url.path
    # Don't intercept API or docs routes — let them return 404 naturally
    api_prefixes = ("/api/", "/asp/", "/health/", "/auth/", "/docs", "/openapi.json", "/redoc", "/metrics")
    if any(path.startswith(p) for p in api_prefixes):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found", "path": path}
        )
    
    # Check for static file first (e.g. /favicon.ico)
    file_path = os.path.join(STATIC_DIR, path.lstrip("/"))
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # Fallback to index.html for React routing
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    return JSONResponse(
        status_code=404,
        content={"message": "UAE PINT AE Engine - Startup in progress or Frontend not built", "docs": "/docs"}
    )
