"""
Recommendation router – exposes LLM recommendation endpoints via FastAPI.
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.recommendation import (
    RecommendationOutput,
    RecommendationResponse,
    RecommendationBulkResponse,
)
from schemas.upload import ErrorResponse
from services.recommendation_service import RecommendationService
from services.risk_scoring import ChainNotFoundError

logger = logging.getLogger("recommendation_router")

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["LLM Security Recommendations"],
)


@router.post(
    "/generate/{chain_id}",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Actionable Security Recommendations",
    description=(
        "Uses Llama 3.3 70B via Groq to synthesize the attack chain, MITRE ATT&CK techniques, "
        "and risk score into concrete SOC analyst recommendations covering Immediate Actions, "
        "Containment, Investigation, and Prevention."
    ),
    responses={
        200: {"description": "Recommendation generated successfully", "model": RecommendationResponse},
        404: {"description": "Attack chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def generate_chain_recommendation(
    chain_id: str,
    force_refresh: bool = Query(
        default=False,
        description="If True, bypasses database cache and forces LLM regeneration.",
    ),
    db: Session = Depends(get_db),
):
    """Generate or retrieve cached security recommendations for an attack chain."""
    try:
        service = RecommendationService(db=db)
        rec_output, is_cached = service.generate_recommendation(
            chain_id_str=chain_id,
            force_refresh=force_refresh,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=RecommendationResponse(
                success=True,
                recommendation_generated=True,
                chain_id=chain_id,
                data=rec_output,
                cached=is_cached,
                message="Recommendation retrieved from cache" if is_cached else "Recommendation generated successfully",
            ).model_dump(),
        )

    except ChainNotFoundError as cne:
        logger.warning(f"Attack chain not found: {cne}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=str(cne)).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Error generating recommendation for chain {chain_id}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Recommendation generation failed: {str(exc)}",
            ).model_dump(),
        )


@router.get(
    "/{chain_id}",
    response_model=RecommendationOutput,
    status_code=status.HTTP_200_OK,
    summary="Get Security Recommendations for an Attack Chain",
    description="Retrieve existing stored recommendations for a specific attack chain.",
    responses={
        200: {"description": "Recommendation retrieved successfully", "model": RecommendationOutput},
        404: {"description": "Recommendation or chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def get_chain_recommendation(chain_id: str, db: Session = Depends(get_db)):
    """Retrieve stored security recommendation for an attack chain."""
    try:
        service = RecommendationService(db=db)
        rec_output = service.get_recommendation(chain_id)

        if not rec_output:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    success=False,
                    message=f"No recommendation found for chain '{chain_id}'. Call POST /generate/{chain_id} first.",
                ).model_dump(),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=rec_output.model_dump(),
        )

    except ChainNotFoundError as cne:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=str(cne)).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Error fetching recommendation: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Failed to fetch recommendation: {str(exc)}",
            ).model_dump(),
        )


@router.post(
    "/generate-all",
    response_model=RecommendationBulkResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Recommendations for All Attack Chains",
    description="Batch process and generate recommendations for all attack chains.",
)
def generate_all_recommendations(
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """Batch generate recommendations for all attack chains."""
    start_time = time.perf_counter()
    try:
        service = RecommendationService(db=db)
        results = service.generate_all_recommendations(force_refresh=force_refresh)

        recommendations = [r[0] for r in results]
        cached_count = sum(1 for r in results if r[1])
        generated_count = len(results) - cached_count
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=RecommendationBulkResponse(
                success=True,
                total_chains=len(results),
                recommendations_generated=generated_count,
                cached_count=cached_count,
                execution_time_ms=round(elapsed_ms, 2),
                recommendations=recommendations,
            ).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Batch recommendation generation failed: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Batch recommendation generation failed: {str(exc)}",
            ).model_dump(),
        )
