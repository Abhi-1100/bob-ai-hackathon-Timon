"""
Pydantic V2 schemas for Risk Scoring results.
Designed for consumption by Threat Analysis Agent, BLUF Report Generator, and Dashboard.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RiskScore(BaseModel):
    """Complete risk score result for a single attack chain."""
    chain_id: str = Field(..., description="Attack chain identifier (e.g. AC001)")
    score: int = Field(..., ge=0, le=100, description="Composite risk score (0-100)")
    level: str = Field(..., description="Risk level: Low, Medium, High, or Critical")
    reasoning: List[str] = Field(
        default_factory=list,
        description="Human-readable explanations for the score",
    )
    event_score: int = Field(default=0, description="Sub-score from event weights")
    mitre_score: int = Field(default=0, description="Sub-score from MITRE technique weights")
    chain_bonus: int = Field(default=0, description="Bonus points from chain length")
    behavioral_score: Optional[int] = Field(default=None, description="Contextual behavioral anomaly score (0-100)")
    behavioral_level: Optional[str] = Field(default=None, description="Behavioral anomaly classification (Normal, Low, Medium, High, Critical)")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extensible metadata for downstream agents",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chain_id": "AC001",
                "score": 92,
                "level": "Critical",
                "reasoning": [
                    "Credential access detected",
                    "Malware activity detected",
                    "Multiple attack stages observed",
                ],
                "event_score": 75,
                "mitre_score": 20,
                "chain_bonus": 10,
                "behavioral_score": 65,
                "behavioral_level": "High",
                "metadata": {},
            }
        }
    )


class RiskScoreResponse(BaseModel):
    """Response for POST /api/v1/risk/calculate/{chain_id}."""
    success: bool = Field(default=True)
    chain_id: str = Field(...)
    score: int = Field(..., ge=0, le=100)
    level: str = Field(...)
    reasoning: List[str] = Field(default_factory=list)
    behavioral_score: Optional[int] = Field(default=None)
    behavioral_level: Optional[str] = Field(default=None)
    message: str = Field(default="Risk score calculated successfully")


class RiskBulkResponse(BaseModel):
    """Response when scoring all attack chains at once."""
    success: bool = Field(default=True)
    chains_scored: int = Field(default=0)
    execution_time_ms: float = Field(default=0.0)
    scores: List[RiskScore] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "chains_scored": 25,
                "execution_time_ms": 120.5,
                "scores": [],
            }
        }
    )


class RiskDistribution(BaseModel):
    """Summary of risk level distribution across all chains."""
    total_chains: int = Field(default=0)
    critical: int = Field(default=0)
    high: int = Field(default=0)
    medium: int = Field(default=0)
    low: int = Field(default=0)
