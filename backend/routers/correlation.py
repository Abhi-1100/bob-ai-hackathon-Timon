"""
Correlation router – exposes the alert correlation engine via FastAPI.
"""

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.attack_chain import CorrelationResult
from schemas.upload import ErrorResponse
from services.alert_correlation import AlertCorrelationEngine, CorrelationError

logger = logging.getLogger("correlation_router")

router = APIRouter(
    prefix="/api/v1/chains",
    tags=["Alert Correlation"],
)


@router.get(
    "/generate",
    response_model=CorrelationResult,
    status_code=status.HTTP_200_OK,
    summary="Generate Attack Chains",
    description=(
        "Fetches all stored alerts from the database, runs the rule-based "
        "correlation engine (source-IP grouping + time-window splitting + "
        "attack-progression ordering), persists the resulting attack chains, "
        "and returns a structured summary.\n\n"
        "**Correlation Rules:**\n"
        "1. Alerts from the same source IP are grouped together.\n"
        "2. A configurable time window (default 30 min) splits distant alerts into separate chains.\n"
        "3. Events are ordered by kill-chain progression (Recon → Exploit → Post-Exploit).\n"
        "4. Alerts against the same destination IP reinforce the grouping.\n\n"
        "*This endpoint is deterministic and does not use AI/LLMs.*"
    ),
    responses={
        200: {
            "description": "Correlation completed and chains stored",
            "model": CorrelationResult,
        },
        400: {
            "description": "No alerts found or correlation failed",
            "model": ErrorResponse,
        },
        500: {
            "description": "Internal server error during correlation",
            "model": ErrorResponse,
        },
    },
)
def generate_attack_chains(db: Session = Depends(get_db)):
    """Run the full correlation pipeline and return the result."""
    try:
        engine = AlertCorrelationEngine(db=db)
        result = engine.correlate(persist=True)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(mode="json"),
        )

    except CorrelationError as ce:
        logger.warning(f"Correlation could not proceed: {ce.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, message=ce.message).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error during correlation: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="An unexpected error occurred during correlation",
            ).model_dump(),
        )
