"""
Pydantic V2 schemas for LangGraph Workflow execution and monitoring.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from schemas.mitre import MitreTechnique
from schemas.risk_score import RiskScore
from schemas.recommendation import RecommendationOutput
from schemas.report import BlufReportOutput


class WorkflowRunResponse(BaseModel):
    """Response returned when invoking POST /api/v1/workflow/run/{chain_id}."""
    success: bool = Field(default=True)
    workflow_status: str = Field(default="completed", description="Status: completed, in_progress, or failed")
    chain_id: str = Field(...)
    data: Optional[Dict[str, Any]] = Field(default=None, description="Compiled outputs from all orchestrated nodes")
    errors: List[str] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)
    message: str = Field(default="Workflow executed successfully")


class WorkflowStatusResponse(BaseModel):
    """Response returned when querying GET /api/v1/workflow/status/{chain_id}."""
    chain_id: str = Field(...)
    status: str = Field(..., description="Overall readiness: completed, in_progress, partial, or missing")
    has_attack_chain: bool = Field(default=False)
    has_mitre_mapping: bool = Field(default=False)
    has_risk_score: bool = Field(default=False)
    has_recommendations: bool = Field(default=False)
    has_report: bool = Field(default=False)
    last_updated: Optional[str] = Field(default=None)


class WorkflowBatchResponse(BaseModel):
    """Response returned when running workflow across all attack chains."""
    success: bool = Field(default=True)
    total_chains: int = Field(default=0)
    completed_chains: int = Field(default=0)
    failed_chains: int = Field(default=0)
    execution_time_ms: float = Field(default=0.0)
    results: List[Dict[str, Any]] = Field(default_factory=list)
