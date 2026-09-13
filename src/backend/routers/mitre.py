"""
MITRE ATT&CK Mapping router – exposes mapping endpoints via FastAPI.
"""

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.mitre import MitreChainMapping, MitreMappingResponse, MitreBulkMappingResponse
from schemas.upload import ErrorResponse
from services.mitre_mapping import MitreMappingService, MitreMappingError

logger = logging.getLogger("mitre_router")

router = APIRouter(
    prefix="/api/v1/mitre",
    tags=["MITRE ATT&CK Mapping"],
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
def map_chain_to_mitre(chain_id: str, db: Session = Depends(get_db)):
    """Map a single attack chain to MITRE ATT&CK techniques."""
    try:
        service = MitreMappingService(db=db)
        result = service.map_single_chain(chain_id)
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
def map_all_chains_to_mitre(db: Session = Depends(get_db)):
    """Map all attack chains to MITRE ATT&CK techniques."""
    try:
        service = MitreMappingService(db=db)
        result = service.map_all_chains()
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
def get_chain_mitre_mappings(chain_id: str, db: Session = Depends(get_db)):
    """Retrieve MITRE ATT&CK mappings for a specific attack chain."""
    try:
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
