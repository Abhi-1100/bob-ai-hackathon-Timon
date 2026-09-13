"""
Workflow router – exposes LangGraph orchestration endpoints via FastAPI.
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.session import get_db
from graph.threat_workflow import ThreatWorkflowRunner
from repositories.attack_chain_repository import AttackChainRepository
from repositories.mitre_repository import MitreRepository
from repositories.risk_repository import RiskRepository
from repositories.recommendation_repository import RecommendationRepository
from repositories.report_repository import ReportRepository
from schemas.workflow import (
    WorkflowRunResponse,
    WorkflowStatusResponse,
    WorkflowBatchResponse,
)
from schemas.upload import ErrorResponse

logger = logging.getLogger("workflow_router")

router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["LangGraph Workflow Orchestration"],
)


@router.post(
    "/run/{chain_id}",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute LangGraph Threat Intelligence Workflow",
    description=(
        "Executes the full automated orchestration workflow for an attack chain: "
        "LoadChain -> MITRE Mapping -> Risk Scoring -> Recommendation Agent -> BLUF Report Agent -> Store Results."
    ),
    responses={
        200: {"description": "Workflow executed successfully", "model": WorkflowRunResponse},
        404: {"description": "Attack chain not found", "model": ErrorResponse},
        500: {"description": "Workflow execution failed", "model": ErrorResponse},
    },
)
def run_workflow(chain_id: str, db: Session = Depends(get_db)):
    """Run end-to-end LangGraph workflow for an attack chain."""
    try:
        runner = ThreatWorkflowRunner(db=db)
        state = runner.run(chain_id)

        workflow_status = state.get("status", "completed")
        errors = state.get("errors", [])
        exec_ms = state.get("execution_metadata", {}).get("execution_time_ms", 0.0)

        if workflow_status == "failed":
            # Check if it was because chain was not found
            if any("not found" in err.lower() for err in errors):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=ErrorResponse(
                        success=False,
                        message=errors[0] if errors else f"Attack chain '{chain_id}' not found",
                    ).model_dump(),
                )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=WorkflowRunResponse(
                    success=False,
                    workflow_status="failed",
                    chain_id=chain_id,
                    errors=errors,
                    execution_time_ms=exec_ms,
                    message="Workflow execution encountered errors",
                ).model_dump(),
            )

        data = {
            "attack_chain": state.get("attack_chain"),
            "mitre_mappings": state.get("mitre_mappings"),
            "risk_score": state.get("risk_score"),
            "recommendations": state.get("recommendations"),
            "report": state.get("report"),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=WorkflowRunResponse(
                success=True,
                workflow_status="completed",
                chain_id=chain_id,
                data=data,
                errors=[],
                execution_time_ms=exec_ms,
                message="Workflow completed successfully",
            ).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error executing workflow for {chain_id}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message=f"Workflow execution failed: {str(exc)}",
            ).model_dump(),
        )


@router.get(
    "/status/{chain_id}",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Threat Intelligence Pipeline Status",
    description="Check the completion state of each pipeline stage for a specific attack chain.",
    responses={
        200: {"description": "Status retrieved successfully", "model": WorkflowStatusResponse},
        404: {"description": "Attack chain not found", "model": ErrorResponse},
    },
)
def get_workflow_status(chain_id: str, db: Session = Depends(get_db)):
    """Check pipeline completion status across all modules for an attack chain."""
    chain_repo = AttackChainRepository(db)
    chain = chain_repo.get_chain(chain_id)

    if not chain:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                success=False,
                message=f"Attack chain '{chain_id}' not found",
            ).model_dump(),
        )

    mitre_repo = MitreRepository(db)
    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)
    rep_repo = ReportRepository(db)

    has_chain = True
    has_mitre = len(mitre_repo.get_chain_mappings(chain.id)) > 0
    has_risk = risk_repo.get_by_chain_id(chain.id) is not None
    has_recs = rec_repo.get_recommendation(chain.id) is not None
    has_rep = rep_repo.get_report(chain.id) is not None

    if has_chain and has_mitre and has_risk and has_recs and has_rep:
        overall_status = "completed"
    elif any([has_mitre, has_risk, has_recs, has_rep]):
        overall_status = "in_progress"
    else:
        overall_status = "pending"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=WorkflowStatusResponse(
            chain_id=chain.chain_id,
            status=overall_status,
            has_attack_chain=has_chain,
            has_mitre_mapping=has_mitre,
            has_risk_score=has_risk,
            has_recommendations=has_recs,
            has_report=has_rep,
            last_updated=chain.start_time.isoformat() if chain.start_time else None,
        ).model_dump(),
    )


@router.post(
    "/run-all",
    response_model=WorkflowBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Workflow for All Attack Chains",
    description="Batch executes the LangGraph workflow across all attack chains in the database.",
)
def run_all_workflows(db: Session = Depends(get_db)):
    """Execute LangGraph workflow across all attack chains."""
    start_time = time.perf_counter()
    chain_repo = AttackChainRepository(db)
    chains = chain_repo.get_all_chains()

    runner = ThreatWorkflowRunner(db=db)
    results = []
    completed_count = 0
    failed_count = 0

    for c in chains:
        state = runner.run(c.chain_id)
        if state.get("status") == "completed":
            completed_count += 1
        else:
            failed_count += 1
        results.append({
            "chain_id": c.chain_id,
            "status": state.get("status"),
            "errors": state.get("errors", []),
        })

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=WorkflowBatchResponse(
            success=True,
            total_chains=len(chains),
            completed_chains=completed_count,
            failed_chains=failed_count,
            execution_time_ms=round(elapsed_ms, 2),
            results=results,
        ).model_dump(),
    )
