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
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:8000 https://*.ngrok-free.dev;"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://erasable-contributively-jann.ngrok-free.dev"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
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
    exempt_prefixes = {"/assets", "/docs", "/openapi.json", "/health", "/metrics", "/auth"}
    exempt_exact = {"/", "/favicon.svg", "/icons.svg"}

    if path in exempt_exact or any(path.startswith(p) for p in exempt_prefixes):
        return await call_next(request)
        
    if not (path.startswith("/api") or path.startswith("/asp")):
        return await call_next(request)

    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not key:
        return JSONResponse(status_code=401, content={"status": "FAILURE", "message": "X-API-Key header required"})
    
    hashed = hashlib.sha256(key.encode()).hexdigest()
    
    # Timing-safe comparison using secrets.compare_digest
    is_valid = False
    tenant_id = None
    for h_key, t_id in VALID_KEYS.items():
        if secrets.compare_digest(h_key, hashed):
            is_valid = True
            tenant_id = t_id
            break

    if not is_valid:
        return JSONResponse(status_code=403, content={"status": "FAILURE", "message": "Invalid API key"})
        
    request.state.tenant_id = tenant_id
    return await call_next(request)

# Exceptions
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

# ── Serve React build ──
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")  
async def health_ready():
    return {"status": "ok"}

# Serve static assets (JS, CSS, images)
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

# Catch-all route — serves index.html for every non-API path
# This fixes React Router (reload on /validate, /history etc works)
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_react(full_path: str):
    # Don't intercept API or docs routes
    api_prefixes = ("api/", "asp/", "health/", "docs", "openapi.json", "redoc")
    if any(full_path.startswith(p) for p in api_prefixes):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    # Fallback if the frontend build isn't ready
    return {"message": "UAE PINT AE Engine", "docs": "/docs"}
