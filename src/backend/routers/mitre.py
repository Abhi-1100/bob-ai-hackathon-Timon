"""
MITRE ATT&CK Mapping router – exposes mapping endpoints via FastAPI.
"""

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import UserDB, AttackChainDB, MitreMappingDB
from routers.auth import get_current_user_obj
from schemas.mitre import MitreChainMapping, MitreMappingResponse, MitreBulkMappingResponse
from schemas.upload import ErrorResponse
from services.mitre_mapping import MitreMappingService, MitreMappingError

logger = logging.getLogger("mitre_router")

router = APIRouter(
    prefix="/api/v1/mitre",
    tags=["MITRE ATT&CK Mapping"],
)


from services.cache_service import cache
from sqlalchemy.orm import joinedload

@router.get(
    "/overview",
    status_code=status.HTTP_200_OK,
    summary="Get Dynamic MITRE ATT&CK Matrix & Technique Breakdown",
    description="Returns dynamic MITRE tactics and techniques aggregated strictly from database attack chains.",
)
def get_mitre_overview(
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Retrieve dynamic MITRE ATT&CK enterprise matrix and technique frequencies."""
    cache_key = f"mitre_overview_{current_user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from collections import defaultdict

        # Eager load attack_chain and its risk_score in 1 single query, strictly scoped to current user
        mappings = (
            db.query(MitreMappingDB)
            .join(AttackChainDB, MitreMappingDB.attack_chain_id == AttackChainDB.id)
            .filter(AttackChainDB.user_id == current_user.id)
            .options(
                joinedload(MitreMappingDB.attack_chain).joinedload(AttackChainDB.risk_score)
            )
            .all()
        )

        if not mappings:
            empty_payload = {
                "total_detected": 0,
                "techniques": [],
                "matrix": [],
            }
            cache.set(cache_key, empty_payload, ttl=300.0)
            return empty_payload

        # Group by technique_id
        tech_map = defaultdict(lambda: {
            "id": "",
            "name": "",
            "tactic": "Unknown",
            "count": 0,
            "chains": set(),
            "severity": "medium",
        })

        for m in mappings:
            t = tech_map[m.technique_id]
            t["id"] = m.technique_id
            t["name"] = m.technique_name
            t["tactic"] = m.tactic or "Execution"
            t["count"] += 1
            if m.attack_chain:
                t["chains"].add(m.attack_chain.chain_id)
                if m.attack_chain.risk_score:
                    lvl = m.attack_chain.risk_score.level.lower()
                    if lvl == "critical" or (lvl == "high" and t["severity"] != "critical"):
                        t["severity"] = lvl

        flat_techniques = [
            {
                "id": v["id"],
                "name": v["name"],
                "tactic": v["tactic"],
                "count": v["count"],
                "chains": list(v["chains"]),
                "severity": v["severity"],
            }
            for v in sorted(tech_map.values(), key=lambda x: x["count"], reverse=True)
        ]

        # Group into tactics for matrix heatmap
        standard_tactics = [
            "Reconnaissance",
            "Initial Access",
            "Execution",
            "Persistence",
            "Privilege Escalation",
            "Credential Access",
            "Discovery",
            "Lateral Movement",
            "Command and Control",
            "Exfiltration",
            "Impact",
        ]

        tactic_buckets = defaultdict(list)
        for tech in flat_techniques:
            tactic_buckets[tech["tactic"]].append(tech)

        matrix = []
        for tac in standard_tactics:
            techs = tactic_buckets.get(tac, [])
            matrix.append({
                "tactic": tac,
                "techniques": techs,
            })

        payload = {
            "total_detected": len(flat_techniques),
            "techniques": flat_techniques,
            "matrix": matrix,
        }
        cache.set(cache_key, payload, ttl=300.0)
        return payload

    except Exception as exc:
        logger.error(f"Error generating MITRE overview: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to retrieve MITRE overview: {str(exc)}"},
        )


@router.post(
    "/map/{chain_id}",
    response_model=MitreMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Map Attack Chain to MITRE ATT&CK",
    description=(
        "Maps all events in the specified attack chain to MITRE ATT&CK techniques "
        "using a deterministic knowledge base. Results are persisted in the database.\n\n"
        "**Mapping is fully deterministic – no AI/LLM is used.**"
    ),
    responses={
        200: {"description": "Mapping completed successfully", "model": MitreMappingResponse},
        404: {"description": "Attack chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def map_chain_to_mitre(
    chain_id: str,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Map a single attack chain to MITRE ATT&CK techniques."""
    try:
        chain = db.query(AttackChainDB).filter(AttackChainDB.chain_id == chain_id, AttackChainDB.user_id == current_user.id).first()
        if not chain:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(success=False, message=f"Attack chain '{chain_id}' not found.").model_dump(),
            )
        service = MitreMappingService(db=db)
        result = service.map_single_chain(chain_id)
        cache.delete(f"mitre_overview_{current_user.id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except MitreMappingError as me:
        logger.warning(f"MITRE mapping failed: {me.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=me.message).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error during MITRE mapping: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="An unexpected error occurred during MITRE mapping",
            ).model_dump(),
        )


@router.post(
    "/map-all",
    response_model=MitreBulkMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Map All Attack Chains to MITRE ATT&CK",
    description=(
        "Maps all stored attack chains to MITRE ATT&CK techniques in bulk. "
        "Existing mappings are cleared and regenerated."
    ),
    responses={
        200: {"description": "Bulk mapping completed", "model": MitreBulkMappingResponse},
        400: {"description": "No attack chains found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def map_all_chains_to_mitre(
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Map all attack chains to MITRE ATT&CK techniques."""
    try:
        service = MitreMappingService(db=db)
        result = service.map_all_chains(user_id=current_user.id)
        cache.delete(f"mitre_overview_{current_user.id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except MitreMappingError as me:
        logger.warning(f"MITRE bulk mapping failed: {me.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, message=me.message).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error during bulk MITRE mapping: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="An unexpected error occurred during MITRE mapping",
            ).model_dump(),
        )


@router.get(
    "/{chain_id}",
    response_model=MitreChainMapping,
    status_code=status.HTTP_200_OK,
    summary="Get MITRE Mappings for Chain",
    description="Retrieve stored MITRE ATT&CK mappings for a specific attack chain.",
    responses={
        200: {"description": "MITRE mappings returned", "model": MitreChainMapping},
        404: {"description": "Chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def get_chain_mitre_mappings(
    chain_id: str,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Retrieve MITRE ATT&CK mappings for a specific attack chain."""
    try:
        chain = db.query(AttackChainDB).filter(AttackChainDB.chain_id == chain_id, AttackChainDB.user_id == current_user.id).first()
        if not chain:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(success=False, message=f"Attack chain '{chain_id}' not found.").model_dump(),
            )
        service = MitreMappingService(db=db)
        result = service.get_chain_mappings(chain_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except MitreMappingError as me:
        logger.warning(f"MITRE get mappings failed: {me.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=me.message).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error retrieving MITRE mappings: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="An unexpected error occurred retrieving MITRE mappings",
            ).model_dump(),
        )

