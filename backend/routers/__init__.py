from .upload import router as upload_router
from .correlation import router as correlation_router
from .mitre import router as mitre_router
from .risk import router as risk_router
from .recommendations import router as recommendation_router
from .reports import router as report_router
from .workflow import router as workflow_router
from .chat import router as chat_router

__all__ = [
    "upload_router",
    "correlation_router",
    "mitre_router",
    "risk_router",
    "recommendation_router",
    "report_router",
    "workflow_router",
    "chat_router",
]

