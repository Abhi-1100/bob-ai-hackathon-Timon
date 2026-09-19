"""
FastAPI Main Application Entry Point.
Threat Intelligence Correlation & Alert Prioritisation Assistant.
"""

import logging
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure current dir (src/backend), src, and repo root are in sys.path
_current_dir = Path(__file__).resolve().parent
_src_dir = _current_dir.parent
_repo_root = _src_dir.parent

for _p in (_current_dir, _src_dir, _repo_root):
    _p_str = str(_p)
    if _p_str not in sys.path:
        sys.path.insert(0, _p_str)

# Automatically load environment variables from .env
for _env_candidate in (_repo_root / ".env", _src_dir / ".env", _current_dir / ".env"):
    if _env_candidate.exists():
        load_dotenv(_env_candidate)
        break
else:
    load_dotenv()


from routers.upload import router as upload_router
from routers.correlation import router as correlation_router
from routers.mitre import router as mitre_router
from routers.risk import router as risk_router
from routers.recommendations import router as recommendation_router
from routers.reports import router as report_router
from routers.workflow import router as workflow_router
from routers.chat import router as chat_router
from routers.dashboard import router as dashboard_router
from routers.auth import router as auth_router
from routers.ingest import router as ingest_router
from routers.stream import router as stream_router
from routers.connectors import router as connectors_router
from routers.metrics import router as metrics_router
from services.live_runtime import runtime
from routers.ingest import router as ingest_router
from services.live_runtime import runtime
from routers.stream import router as stream_router
from routers.connectors import router as connectors_router

# Configure production-ready structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("threat_intel_backend")

app = FastAPI(
    title="Threat Intelligence Correlation & Alert Prioritisation Assistant",
    version="1.0.0",
    description=(
        "Backend API for ingesting multi-source security feeds (SIEM, satellite, sensors, OSINT), "
        "correlating threats, mapping to MITRE ATT&CK®, and generating commander-ready BLUF summaries."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(stream_router)
app.include_router(connectors_router)
app.include_router(metrics_router)
app.include_router(upload_router)
app.include_router(dashboard_router)
app.include_router(correlation_router)
app.include_router(mitre_router)
app.include_router(risk_router)
app.include_router(recommendation_router)
app.include_router(report_router)
app.include_router(workflow_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup():
    """Ensure database tables exist on startup."""
    try:
        from database.session import _get_engine
        from database.models import Base
        engine = _get_engine()
        Base.metadata.create_all(bind=engine)
        from database.schema_upgrade import ensure_streaming_columns
        ensure_streaming_columns(engine)
        logger.info("Database tables verified on startup.")
    except Exception as exc:
        logger.warning(f"Database initialization warning on startup: {exc}")


@app.on_event("startup")
async def start_live_runtime():
    """Start the in-process deterministic streaming worker."""
    await runtime.start()


@app.on_event("shutdown")
async def stop_live_runtime():
    await runtime.stop()


@app.get("/", tags=["Health"])
async def root_health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "Threat Intelligence Correlation & Alert Prioritisation Assistant",
        "version": "1.0.0",
    }


@app.get("/api/demo/security-alerts", tags=["Demo"])
async def demo_security_alerts():
    """Local demonstration feed. URL ingestion still rejects localhost to preserve SSRF controls."""
    return {"alerts": [
        {"alert_id": "AC001-01", "timestamp": "2026-09-19T10:00:00Z", "src_ip": "45.20.10.5", "dst_ip": "10.0.0.5", "event_type": "PORT_SCAN", "severity": "MEDIUM", "description": "Multiple ports scanned"},
        {"alert_id": "AC001-02", "timestamp": "2026-09-19T10:05:00Z", "src_ip": "45.20.10.5", "dst_ip": "10.0.0.5", "event_type": "FAILED_LOGIN", "severity": "HIGH", "description": "Multiple failed login attempts"},
    ]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
