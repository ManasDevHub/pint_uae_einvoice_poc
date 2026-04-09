from fastapi import APIRouter
from datetime import datetime, timezone
import time
import os

router = APIRouter()
START_TIME = time.time()

@router.get("/live")
async def liveness():
    """Process is running. Kubernetes liveness probe."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/ready")
async def readiness():
    """All dependencies reachable. Kubernetes readiness probe."""
    checks = {}
    overall = "ok"
    # Check Db
    try:
        from sqlalchemy import create_engine
        from app.core.config import settings
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            pass
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = str(e)
        overall = "degraded"
        
    uptime = round(time.time() - START_TIME, 1)
    return {"status": overall, "checks": checks, "uptime_seconds": uptime}
