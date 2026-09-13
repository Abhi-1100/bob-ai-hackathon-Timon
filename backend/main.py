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

# Automatically load environment variables from .env
_root_env = Path(__file__).resolve().parent.parent / ".env"
_backend_env = Path(__file__).resolve().parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env)
elif _backend_env.exists():
    load_dotenv(_backend_env)
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(upload_router)
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
        logger.info("Database tables verified on startup.")
    except Exception as exc:
        logger.warning(f"Database initialization warning on startup: {exc}")


@app.get("/", tags=["Health"])
async def root_health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "Threat Intelligence Correlation & Alert Prioritisation Assistant",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
