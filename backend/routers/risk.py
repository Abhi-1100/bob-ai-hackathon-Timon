"""
Risk Scoring router – exposes deterministic risk scoring endpoints via FastAPI.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.risk_score import RiskScore, RiskScoreResponse, RiskBulkResponse, RiskDistribution
from schemas.upload import ErrorResponse
from services.risk_scoring import RiskScoringEngine, ChainNotFoundError, RiskScoringError

logger = logging.getLogger("risk_router")

router = APIRouter(
    prefix="/api/v1/risk",
    tags=["Risk Scoring Engine"],
)


@router.post(
    "/calculate/{chain_id}",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Risk Score for an Attack Chain",
    description=(
        "Calculates threat risk score (0-100), assigns severity level (Low, Medium, High, Critical), "
        "and generates explainable reasoning based on event weights, MITRE tactics, and chain progression.\n\n"
        "**Scoring is fully deterministic – no LLM or AI is used.**"
    ),
    responses={
        200: {"description": "Risk score calculated and saved successfully", "model": RiskScoreResponse},
        404: {"description": "Attack chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def calculate_chain_risk(chain_id: str, db: Session = Depends(get_db)):
    """Calculate and store risk score for a single attack chain."""
    try:
        engine = RiskScoringEngine(db=db)
        score_obj = engine.calculate_and_store_for_chain(chain_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "chain_id": score_obj.chain_id,
                "score": score_obj.score,
                "level": score_obj.level,
                "reasoning": score_obj.reasoning,
                "message": "Risk score calculated successfully",
            },
        )

    except ChainNotFoundError as cne:
        logger.warning(f"Chain not found: {cne}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=str(cne)).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error calculating risk score: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Risk scoring failed: {str(exc)}",
            ).model_dump(),
        )


@router.get(
    "/{chain_id}",
    response_model=RiskScore,
    status_code=status.HTTP_200_OK,
    summary="Get Risk Score for an Attack Chain",
    description="Retrieve the pre-calculated risk score and explainable reasoning for a specific attack chain.",
    responses={
        200: {"description": "Risk score retrieved successfully", "model": RiskScore},
        404: {"description": "Risk score or chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def get_chain_risk(chain_id: str, db: Session = Depends(get_db)):
    """Retrieve existing stored risk score for an attack chain."""
    try:
        engine = RiskScoringEngine(db=db)
        score_obj = engine.get_stored_score(chain_id)

        if not score_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    success=False,
                    message=f"No risk score found for chain '{chain_id}'. Run POST /calculate/{chain_id} first.",
                ).model_dump(),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=score_obj.model_dump(),
        )

    except ChainNotFoundError as cne:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=str(cne)).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Error fetching risk score: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Failed to fetch risk score: {str(exc)}",
            ).model_dump(),
        )


@router.post(
    "/calculate-all",
    response_model=RiskBulkResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Risk Scores for All Attack Chains",
    description="Calculates risk scores for all stored attack chains and returns them prioritized by score descending.",
    responses={
        200: {"description": "All attack chains scored successfully", "model": RiskBulkResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def calculate_all_risk(db: Session = Depends(get_db)):
    """Bulk-calculate and prioritize risk scores for all attack chains."""
    import time
    start_time = time.perf_counter()
    try:
        engine = RiskScoringEngine(db=db)
        scores = engine.score_all_chains()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=RiskBulkResponse(
                success=True,
                chains_scored=len(scores),
                execution_time_ms=round(elapsed_ms, 2),
                scores=scores,
            ).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Bulk risk scoring failed: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Bulk risk scoring failed: {str(exc)}",
            ).model_dump(),
        )


@router.get(
    "/summary/distribution",
    response_model=RiskDistribution,
    status_code=status.HTTP_200_OK,
    summary="Get Risk Severity Distribution Summary",
    description="Returns aggregate counts of attack chains categorized into Critical, High, Medium, and Low risk.",
)
def get_risk_distribution(db: Session = Depends(get_db)):
    """Retrieve distribution of attack chains across risk levels."""
    try:
        engine = RiskScoringEngine(db=db)
        distribution = engine.get_risk_distribution()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=distribution.model_dump(),
        )
    except Exception as exc:
        logger.error(f"Failed to get risk distribution: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Failed to retrieve risk distribution: {str(exc)}",
            ).model_dump(),
        )
