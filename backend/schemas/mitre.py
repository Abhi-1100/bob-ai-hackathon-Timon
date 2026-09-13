"""
Pydantic V2 schemas for MITRE ATT&CK mappings.
Designed for consumption by Risk Scoring, Threat Analysis Agent, and BLUF Report Generator.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class MitreTechnique(BaseModel):
    """A single MITRE ATT&CK technique mapping."""
    technique_id: str = Field(..., description="MITRE ATT&CK technique ID (e.g. T1595)")
    name: str = Field(..., description="Human-readable technique name (e.g. Active Scanning)")
    tactic: str = Field(default="Unknown", description="MITRE ATT&CK tactic category (e.g. Reconnaissance)")
    description: str = Field(default="", description="Brief description of the technique")
    event: str = Field(default="", description="Original alert event that triggered this mapping")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "technique_id": "T1595",
                "name": "Active Scanning",
                "tactic": "Reconnaissance",
                "description": "Adversaries may scan victim IP blocks to gather information.",
                "event": "PortScan",
            }
        }
    )


class MitreChainMapping(BaseModel):
    """Complete MITRE ATT&CK mapping result for a single attack chain."""
    chain_id: str = Field(..., description="Attack chain identifier (e.g. AC001)")
    techniques: List[MitreTechnique] = Field(
        default_factory=list,
        description="List of mapped MITRE ATT&CK techniques",
    )
    techniques_found: int = Field(default=0, description="Number of techniques mapped")
    unmapped_events: List[str] = Field(
        default_factory=list,
        description="Events that could not be mapped to known techniques",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extensible metadata for downstream scoring and reporting",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chain_id": "AC001",
                "techniques": [
                    {"technique_id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance", "description": "", "event": "PortScan"},
                    {"technique_id": "T1110", "name": "Brute Force", "tactic": "Credential Access", "description": "", "event": "BruteForce"},
                ],
                "techniques_found": 2,
                "unmapped_events": [],
                "metadata": {},
            }
        }
    )


class MitreMappingResponse(BaseModel):
    """Response for POST /api/v1/mitre/map/{chain_id}."""
    success: bool = Field(default=True)
    chain_id: str = Field(...)
    techniques_found: int = Field(default=0)
    unmapped_events: List[str] = Field(default_factory=list)
    message: str = Field(default="MITRE mapping completed successfully")


class MitreBulkMappingResponse(BaseModel):
    """Response when mapping all attack chains at once."""
    success: bool = Field(default=True)
    chains_mapped: int = Field(default=0, description="Number of chains processed")
    total_techniques: int = Field(default=0, description="Total technique mappings created")
    execution_time_ms: float = Field(default=0.0)
    mappings: List[MitreChainMapping] = Field(default_factory=list)
