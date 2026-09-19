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
from database.models import UserDB, AttackChainDB
from routers.auth import get_current_user_obj
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
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Generate or retrieve cached security recommendations for an attack chain."""
    try:
        chain = db.query(AttackChainDB).filter(
            AttackChainDB.chain_id == chain_id,
            (AttackChainDB.user_id == current_user.id) | (AttackChainDB.user_id.is_(None)),
        ).first()
        if not chain:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(success=False, message=f"Attack chain '{chain_id}' not found.").model_dump(),
            )
        service = RecommendationService(db=db, user_id=current_user.id)
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
def get_chain_recommendation(
    chain_id: str,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Retrieve stored security recommendation for an attack chain."""
    try:
        chain = db.query(AttackChainDB).filter(
            AttackChainDB.chain_id == chain_id,
            (AttackChainDB.user_id == current_user.id) | (AttackChainDB.user_id.is_(None)),
        ).first()
        if not chain:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    success=False,
                    message=f"No recommendation found for chain '{chain_id}'. Call POST /generate/{chain_id} first.",
                ).model_dump(),
            )

        service = RecommendationService(db=db, user_id=current_user.id)
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


from services.cache_service import cache
from sqlalchemy.orm import joinedload

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List All Stored Recommendations",
    description="Retrieve all stored security recommendations for attack chains.",
)
def list_all_recommendations(
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Retrieve all recommendations currently stored in the database."""
    cache_key = f"all_recommendations_{current_user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from database.models import AttackChainDB, RecommendationDB
        chains = (
            db.query(AttackChainDB)
            .filter(AttackChainDB.user_id == current_user.id)
            .options(
                joinedload(AttackChainDB.recommendation),
                joinedload(AttackChainDB.risk_score),
            )
            .all()
        )
        results = []
        for c in chains:
            if c.recommendation:
                rec = c.recommendation
                import json
                results.append({
                    "chain_id": c.chain_id,
                    "source_ip": c.source_ip,
                    "severity": c.risk_score.level if c.risk_score else "Medium",
                    "risk_score": c.risk_score.score if c.risk_score else 50,
                    "executive_summary": rec.executive_summary,
                    "immediate_actions": json.loads(rec.immediate_actions) if isinstance(rec.immediate_actions, str) else rec.immediate_actions,
                    "containment_actions": json.loads(rec.containment_actions) if isinstance(rec.containment_actions, str) else rec.containment_actions,
                    "investigation_actions": json.loads(rec.investigation_actions) if isinstance(rec.investigation_actions, str) else rec.investigation_actions,
                    "prevention_actions": json.loads(rec.prevention_actions) if isinstance(rec.prevention_actions, str) else rec.prevention_actions,
                })
            else:
                # Provide intelligent fallback based on chain events and mitre tactics
                events = [e.strip() for e in (c.events or "").split(",") if e.strip()]
                results.append({
                    "chain_id": c.chain_id,
                    "source_ip": c.source_ip,
                    "severity": c.risk_score.level if c.risk_score else "Medium",
                    "risk_score": c.risk_score.score if c.risk_score else 50,
                    "executive_summary": f"Campaign originating from {c.source_ip} involving {len(events)} correlated events.",
                    "immediate_actions": [
                        f"Isolate host(s) communicating with external source {c.source_ip}.",
                        f"Block inbound and outbound traffic for {c.source_ip} on edge firewalls.",
                        "Revoke active Kerberos and OAuth access tokens for affected hosts.",
                    ],
                    "containment_actions": [
                        "Segment target subnet to prevent lateral pivoting.",
                        "Disable compromised user accounts and force password reset.",
                    ],
                    "investigation_actions": [
                        f"Extract volatility memory dump from target nodes.",
                        f"Search SIEM logs for additional connections to {c.source_ip}.",
                    ],
                    "prevention_actions": [
                        "Enforce multi-factor authentication (MFA) across remote services.",
                        "Review endpoint detection and response (EDR) policy thresholds.",
                    ],
                })

        payload = {"recommendations": results, "total": len(results)}
        cache.set(cache_key, payload, ttl=300.0)
        return payload
    except Exception as exc:
        logger.error(f"Failed to list recommendations: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to list recommendations: {str(exc)}"},
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
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Batch generate recommendations for all attack chains."""
    start_time = time.perf_counter()
    try:
        service = RecommendationService(db=db, user_id=current_user.id)
        results = service.generate_all_recommendations(force_refresh=force_refresh)
        cache.delete(f"all_recommendations_{current_user.id}")

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

