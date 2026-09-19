"""
Pydantic V2 schemas for the Behavioral + Context Analysis Layer.

These schemas carry structured, explainable anomaly evidence across
the LangGraph workflow and out to the API/frontend.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Per-Dimension Signal
# ---------------------------------------------------------------------------
class DimensionSignal(BaseModel):
    """
    Captures the anomaly contribution and human-readable signals
    for a single behavioral dimension (Identity, Device, Network, etc.).
    """
    dimension: str = Field(..., description="Dimension name (e.g. identity, device, network)")
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Normalised anomaly contribution for this dimension (0-100)",
    )
    signals: List[str] = Field(
        default_factory=list,
        description="Human-readable signal descriptions observed in this dimension",
    )
    available: bool = Field(
        default=True,
        description="False when telemetry for this dimension was not present in the data",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dimension": "network",
                "score": 45.0,
                "signals": ["New external IP", "IP not previously seen for this user"],
                "available": True,
            }
        }
    )


# ---------------------------------------------------------------------------
# Full Behavioral Analysis Result
# ---------------------------------------------------------------------------
class BehavioralAnalysisResult(BaseModel):
    """
    Complete output of the Behavioral + Context Analysis engine for one attack chain.

    anomaly_score is 0-100 (higher = more anomalous/suspicious).
    It is NOT a verdict — it is contextual evidence for the analyst.
    """
    chain_id: str = Field(..., description="Attack chain identifier (e.g. AC001)")
    anomaly_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Composite behavioural anomaly score (0-100)",
    )
    anomaly_level: str = Field(
        ...,
        description="Human label: Normal (<25), Low (25-40), Elevated (40-60), High (60-80), Critical (>80)",
    )
    signals: List[str] = Field(
        default_factory=list,
        description="Top contributing signals across all dimensions",
    )
    behavior_status: str = Field(
        default="NORMAL",
        description="System behavioral status: NORMAL, ANOMALOUS, SUSPICIOUS, HIGH RISK",
    )
    context_tags: List[str] = Field(
        default_factory=list,
        description="Dynamic evidence-based context tags",
    )
    behavioral_reasons: List[str] = Field(
        default_factory=list,
        description="Structured reasons why this was flagged",
    )
    analyst_disposition: str = Field(
        default="NEEDS_REVIEW",
        description="Analyst disposition: NEEDS_REVIEW, BENIGN_ACTIVITY, AUTHORIZED_ACTIVITY, FALSE_POSITIVE, TRUE_POSITIVE, CONFIRMED_INCIDENT",
    )
    dimension_breakdown: Dict[str, DimensionSignal] = Field(
        default_factory=dict,
        description="Per-dimension anomaly scores and signals",
    )
    why_prioritized: str = Field(
        default="",
        description="One-sentence analyst-facing explanation of why this chain was elevated",
    )
    # Baseline context
    source_ip: Optional[str] = Field(default=None)
    entity_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Entity-level context (known/unknown, first-seen, baseline deviation)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chain_id": "AC001",
                "anomaly_score": 72.0,
                "anomaly_level": "High",
                "behavior_status": "SUSPICIOUS",
                "context_tags": ["UNKNOWN IP", "NEW TARGET", "HIGH VELOCITY", "UNUSUAL TIME"],
                "behavioral_reasons": [
                    "IP address observed for the first time",
                    "High-velocity burst activity",
                    "Activity outside normal business hours",
                ],
                "analyst_disposition": "NEEDS_REVIEW",
                "signals": [
                    "Unknown source IP",
                    "High event velocity — 3x above baseline",
                    "First-time access to critical target",
                    "Activity outside normal business hours",
                ],
                "dimension_breakdown": {},
                "why_prioritized": "Combination of unknown origin, high velocity, and critical target raises analyst priority.",
            }
        }
    )


# ---------------------------------------------------------------------------
# Lightweight context block for API responses
# ---------------------------------------------------------------------------
class BehavioralContext(BaseModel):
    """
    Compact behavioral context embedded in the attack chain API response.
    Extends the existing chain detail without breaking existing fields.
    """
    anomaly_score: float = Field(default=0.0, ge=0.0, le=100.0)
    anomaly_level: str = Field(default="Normal")
    behavior_status: str = Field(default="NORMAL")
    context_tags: List[str] = Field(default_factory=list)
    behavioral_reasons: List[str] = Field(default_factory=list)
    analyst_disposition: str = Field(default="NEEDS_REVIEW")
    signals: List[str] = Field(default_factory=list)
    contributing_signals: List[str] = Field(default_factory=list)
    dimension_breakdown: Dict[str, Any] = Field(default_factory=dict)
    why_prioritized: str = Field(default="")
    entity_context: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Analyst Disposition Request Schema
# ---------------------------------------------------------------------------
class DispositionUpdateRequest(BaseModel):
    """Payload to update an attack chain's analyst disposition."""
    disposition: str = Field(
        ...,
        description="One of: NEEDS_REVIEW, BENIGN_ACTIVITY, AUTHORIZED_ACTIVITY, FALSE_POSITIVE, TRUE_POSITIVE, CONFIRMED_INCIDENT",
    )


# ---------------------------------------------------------------------------
# Baseline snapshot (used internally and for API debugging)
# ---------------------------------------------------------------------------
class EntityBaseline(BaseModel):
    """Snapshot of a computed entity baseline."""
    entity_type: str = Field(..., description="Entity category: ip, user, device, target")
    entity_value: str = Field(..., description="Entity identifier value")
    observation_count: int = Field(default=0, description="Number of historical observations")
    avg_events_per_hour: float = Field(default=0.0)
    peak_events_per_hour: float = Field(default=0.0)
    common_hours: List[int] = Field(default_factory=list, description="Most common active hours (0-23)")
    first_seen: Optional[str] = Field(default=None)
    last_seen: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
