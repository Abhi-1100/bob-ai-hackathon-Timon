"""
Alert schema definitions for Threat Intelligence Correlation & Alert Prioritisation Assistant.
Designed for consumption by CSV Parser, Correlation Engine, MITRE Mapper, and LangGraph Agents.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AlertSeverity(str, Enum):
    """Allowed normalized severity levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Alert(BaseModel):
    """
    Canonical Alert schema representing an ingested and validated security alert.
    """
    alert_id: str = Field(
        default_factory=lambda: f"ALT-{uuid.uuid4().hex[:8].upper()}",
        description="Unique identifier for downstream correlation and attack graph tracking",
    )
    timestamp: datetime = Field(
        ...,
        description="Event timestamp in UTC ISO format",
    )
    src_ip: str = Field(
        ...,
        description="Source IP address or hostname",
    )
    dst_ip: str = Field(
        ...,
        description="Destination IP address or hostname",
    )
    event: str = Field(
        ...,
        description="Normalized security event name (e.g. PortScan, BruteForce)",
    )
    severity: AlertSeverity = Field(
        ...,
        description="Standardized severity level (Low, Medium, High, Critical)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for LangGraph agents, MITRE mapping, or scoring",
    )

    @field_validator("severity", mode="before")
    @classmethod
    def validate_severity_str(cls, value: Any) -> AlertSeverity:
        if isinstance(value, AlertSeverity):
            return value
        if isinstance(value, str):
            normalized = value.strip().capitalize()
            # Match against known enum values
            for sev in AlertSeverity:
                if sev.value.lower() == normalized.lower():
                    return sev
        raise ValueError(
            f"Invalid severity '{value}'. Allowed values: {[s.value for s in AlertSeverity]}"
        )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "alert_id": "ALT-8F92A1B4",
                "timestamp": "2026-09-13T10:01:00Z",
                "src_ip": "10.0.0.1",
                "dst_ip": "10.0.0.5",
                "event": "PortScan",
                "severity": "Medium",
                "metadata": {},
            }
        },
    )


class ParseResult(BaseModel):
    """
    Standard output structure returned by the CSV Parser.
    """
    total_rows: int = Field(..., description="Total rows read from CSV after initial load")
    valid_rows: int = Field(..., description="Number of rows successfully parsed into Alert objects")
    invalid_rows: int = Field(..., description="Number of malformed or invalid rows skipped")
    alerts: List[Alert] = Field(..., description="List of validated Alert objects")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_rows": 5000,
                "valid_rows": 4980,
                "invalid_rows": 20,
                "alerts": [],
            }
        }
    )
