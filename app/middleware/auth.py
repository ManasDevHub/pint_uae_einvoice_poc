from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
from app.core.config import settings

VALID_KEYS = {
    hashlib.sha256(k.encode()).hexdigest(): k
    for k in settings.api_keys.split(",") if k
}

class APIKeyMiddleware(BaseHTTPMiddleware):
    # Routes that don't require API key validation
    EXEMPT_PREFIXES = {"/assets", "/docs", "/openapi.json", "/health", "/metrics", "/docs", "/redoc", "/auth"}
    EXEMPT_EXACT = {"/", "/favicon.svg", "/icons.svg"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Exempt exact matches or path prefixes
        if path in self.EXEMPT_EXACT or any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return await call_next(request)
            
        # Also exempt any path that doesn't start with our API prefixes
        if not (path.startswith("/api") or path.startswith("/asp")):
            return await call_next(request)

        key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if not key:
            return await self._error_response(401, "X-API-Key header required")
        hashed = hashlib.sha256(key.encode()).hexdigest()
        if hashed not in VALID_KEYS:
            return await self._error_response(403, "Invalid API key")
        request.state.tenant_id = VALID_KEYS[hashed]
        return await call_next(request)

    async def _error_response(self, status: int, detail: str):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=status, content={"status": "FAILURE", "message": detail})
