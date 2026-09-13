"""
Pydantic V2 schemas for Attack Chains produced by the Alert Correlation Engine.
Designed for consumption by Risk Scoring, MITRE Mapping, and LangGraph Agents.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AttackChainAlert(BaseModel):
    """Minimal alert reference embedded inside an attack chain."""
    alert_id: str = Field(..., description="UUID of the original alert record")
    timestamp: datetime = Field(..., description="When the alert fired")
    event: str = Field(..., description="Normalized event name")
    severity: str = Field(..., description="Normalized severity level")
    dst_ip: str = Field(..., description="Destination IP targeted by this alert")


class AttackChain(BaseModel):
    """
    A correlated group of alerts that form a coherent attack progression.
    Produced by the rule-based Correlation Engine.
    """
    chain_id: str = Field(
        ...,
        description="Human-readable chain identifier (e.g. AC001)",
    )
    source_ip: str = Field(
        ...,
        description="Common source IP that links all alerts in this chain",
    )
    destination_ips: List[str] = Field(
        default_factory=list,
        description="Unique destination IPs targeted across the chain",
    )
    start_time: datetime = Field(
        ...,
        description="Timestamp of the earliest alert in the chain",
    )
    end_time: datetime = Field(
        ...,
        description="Timestamp of the latest alert in the chain",
    )
    events: List[str] = Field(
        default_factory=list,
        description="Ordered list of unique event types in the chain progression",
    )
    severity_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of alerts per severity level (e.g. {'High': 3, 'Medium': 5})",
    )
    alert_count: int = Field(
        ...,
        description="Total number of alerts grouped into this chain",
    )
    alerts: List[AttackChainAlert] = Field(
        default_factory=list,
        description="Individual alert records belonging to this chain",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extensible metadata for downstream MITRE mapping and risk scoring",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chain_id": "AC001",
                "source_ip": "10.0.0.1",
                "destination_ips": ["10.0.0.5"],
                "start_time": "2026-09-13T10:00:00Z",
                "end_time": "2026-09-13T10:15:00Z",
                "events": ["PortScan", "BruteForce", "Malware"],
                "severity_summary": {"Medium": 1, "High": 1, "Critical": 1},
                "alert_count": 3,
                "alerts": [],
                "metadata": {},
            }
        }
    )


class CorrelationResult(BaseModel):
    """Summary returned after the correlation engine processes alerts."""
    chains_created: int = Field(..., description="Number of attack chains generated")
    alerts_processed: int = Field(..., description="Total alerts that were analysed")
    execution_time_ms: float = Field(..., description="Time taken in milliseconds")
    chains: List[AttackChain] = Field(
        default_factory=list,
        description="Full list of generated attack chains",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chains_created": 25,
                "alerts_processed": 10000,
                "execution_time_ms": 2340.5,
                "chains": [],
            }
        }
    )
