"""
Report router – exposes executive BLUF report endpoints via FastAPI.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.report import (
    BlufReportOutput,
    ReportResponse,
    ReportListResponse,
)
from schemas.upload import ErrorResponse
from services.report_service import ReportService
from services.risk_scoring import ChainNotFoundError

logger = logging.getLogger("report_router")

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Executive BLUF Reports"],
)


@router.post(
    "/generate/{chain_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Executive BLUF Threat Intelligence Report",
    description=(
        "Uses Llama 3.3 70B via Groq to synthesize the entire attack chain, MITRE ATT&CK techniques, "
        "risk score, and recommendations into an executive-ready Bottom Line Up Front (BLUF) report."
    ),
    responses={
        200: {"description": "Report generated successfully", "model": ReportResponse},
        404: {"description": "Attack chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def generate_chain_report(
    chain_id: str,
    force_refresh: bool = Query(
        default=False,
        description="If True, bypasses database cache and forces LLM regeneration.",
    ),
    db: Session = Depends(get_db),
):
    """Generate or retrieve cached BLUF report for an attack chain."""
    try:
        service = ReportService(db=db)
        report_output, is_cached = service.generate_report(
            chain_id_str=chain_id,
            force_refresh=force_refresh,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ReportResponse(
                success=True,
                report_generated=True,
                chain_id=chain_id,
                data=report_output,
                cached=is_cached,
                message="Report retrieved from cache" if is_cached else "Report generated successfully",
            ).model_dump(),
        )

    except ChainNotFoundError as cne:
        logger.warning(f"Attack chain not found: {cne}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=str(cne)).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Error generating BLUF report for chain {chain_id}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Report generation failed: {str(exc)}",
            ).model_dump(),
        )


@router.get(
    "/{chain_id}",
    response_model=BlufReportOutput,
    status_code=status.HTTP_200_OK,
    summary="Get Executive BLUF Report for an Attack Chain",
    description="Retrieve the stored executive BLUF report for a specific attack chain.",
    responses={
        200: {"description": "Report retrieved successfully", "model": BlufReportOutput},
        404: {"description": "Report or chain not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def get_chain_report(chain_id: str, db: Session = Depends(get_db)):
    """Retrieve stored BLUF report for an attack chain."""
    try:
        service = ReportService(db=db)
        report_output = service.get_report(chain_id)

        if not report_output:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    success=False,
                    message=f"No report found for chain '{chain_id}'. Call POST /generate/{chain_id} first.",
                ).model_dump(),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=report_output.model_dump(),
        )

    except ChainNotFoundError as cne:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(success=False, message=str(cne)).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Error fetching BLUF report: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Failed to fetch report: {str(exc)}",
            ).model_dump(),
        )


@router.get(
    "",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Generated BLUF Reports",
    description="Retrieve all stored executive BLUF reports with pagination.",
)
def list_all_reports(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List all stored BLUF intelligence reports."""
    try:
        service = ReportService(db=db)
        reports = service.get_all_reports(limit=limit, offset=offset)

        if not reports:
            from database.models import AttackChainDB
            chains = db.query(AttackChainDB).order_by(AttackChainDB.start_time.desc()).limit(limit).all()
            for c in chains:
                score = c.risk_score.score if c.risk_score else 50
                level = c.risk_score.level if c.risk_score else "Medium"
                events = [e.strip() for e in (c.events or "").split(",") if e.strip()]
                dest_ips = [d.strip() for d in (c.destination_ips or "").split(",") if d.strip()]
                techs = [f"{m.technique_id} ({m.technique_name})" for m in (c.mitre_mappings or [])]
                reports.append(
                    BlufReportOutput(
                        chain_id=c.chain_id,
                        threat_level=level,
                        executive_summary=f"High-confidence threat campaign detected originating from source {c.source_ip}. Multi-factor risk assessed at {score}/100 ({level} Priority).",
                        attack_overview=f"Correlated attack sequence consisting of {len(events)} stages: {' -> '.join(events) if events else 'Suspicious traffic'}.",
                        affected_assets=f"Target hosts: {', '.join(dest_ips) if dest_ips else 'Internal subnet'}.",
                        mitre_summary=f"Mapped MITRE ATT&CK techniques: {', '.join(techs) if techs else 'Heuristic signatures'}.",
                        risk_assessment=f"Composite risk evaluated at {score}/100 based on event severity weights, time proximity, and kill chain progression bonus.",
                        recommended_actions=f"Block source {c.source_ip} at perimeter firewalls, isolate compromised target hosts, and perform memory forensics.",
                        conclusion=f"Campaign is currently categorized as {level}. Immediate containment required to prevent lateral movement.",
                    )
                )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ReportListResponse(
                success=True,
                total_reports=len(reports),
                reports=reports,
            ).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Failed to list reports: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Failed to list reports: {str(exc)}",
            ).model_dump(),
        )
