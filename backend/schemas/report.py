"""
Pydantic V2 schemas for Executive BLUF Threat Intelligence Reports.
Designed for consumption by Dashboards, PDF Exporters, Executives, and AI Analyst Chat.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BlufReportOutput(BaseModel):
    """Structured BLUF (Bottom Line Up Front) intelligence report for an attack chain."""
    chain_id: str = Field(..., description="Attack chain identifier (e.g. AC001)")
    threat_level: str = Field(..., description="Threat severity level: Critical, High, Medium, or Low")
    executive_summary: str = Field(
        ...,
        description="Concise C-level summary (<100 words) answering What happened, Why it matters, and What should be done",
    )
    attack_overview: str = Field(
        ...,
        description="Chronological description of attack progression, stages, and adversary behavior",
    )
    affected_assets: str = Field(
        ...,
        description="Targeted endpoints, source and destination IP addresses, and impacted subnets",
    )
    mitre_summary: str = Field(
        ...,
        description="Analysis of mapped MITRE ATT&CK techniques and suspected adversary objectives",
    )
    risk_assessment: str = Field(
        ...,
        description="Breakdown of why the risk score was assigned, potential business impact, and severity justification",
    )
    recommended_actions: str = Field(
        ...,
        description="Synthesis of critical containment, investigation, recovery, and prevention actions",
    )
    conclusion: str = Field(
        ...,
        description="Final intelligence analyst assessment and immediate next strategic milestones",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chain_id": "AC001",
                "threat_level": "Critical",
                "executive_summary": (
                    "A multi-stage intrusion originated from 192.168.1.100 targeting server 10.0.0.5, "
                    "escalating from reconnaissance to credential theft and malware execution. This represents "
                    "an active compromise with severe operational risk. Immediate host isolation and credential "
                    "revocation are required to avert lateral movement."
                ),
                "attack_overview": (
                    "The adversary initiated an active port scan followed by an automated brute-force attack against "
                    "SSH/RDP services. Following initial access, memory dumping tools were deployed to harvest "
                    "credentials, culminating in binary malware execution."
                ),
                "affected_assets": "Target server 10.0.0.5 (Finance Subnet); Attacker Source IP: 192.168.1.100.",
                "mitre_summary": (
                    "Mapped techniques include T1595 (Active Scanning), T1110 (Brute Force), T1003 (Credential Dumping), "
                    "and T1204 (User Execution), indicating an adversary executing a structured intrusion lifecycle."
                ),
                "risk_assessment": (
                    "Risk score 92/100 (Critical). High likelihood of complete host takeover and potential data compromise "
                    "driven by observed credential access and malware payload deployment."
                ),
                "recommended_actions": (
                    "1. Isolate 10.0.0.5 from corporate VLAN.\n"
                    "2. Block source IP 192.168.1.100 at boundary firewall.\n"
                    "3. Reset all enterprise administrative passwords.\n"
                    "4. Enable Windows Defender Credential Guard."
                ),
                "conclusion": (
                    "Active containment is in progress. Forensic triage of host memory is recommended as the next immediate step."
                ),
            }
        }
    )


class ReportResponse(BaseModel):
    """API response for POST /api/v1/reports/generate/{chain_id}."""
    success: bool = Field(default=True)
    report_generated: bool = Field(default=True)
    chain_id: str = Field(...)
    data: Optional[BlufReportOutput] = Field(default=None)
    cached: bool = Field(default=False, description="True if served from database cache")
    message: str = Field(default="BLUF report generated successfully")


class ReportListResponse(BaseModel):
    """API response for GET /api/v1/reports."""
    success: bool = Field(default=True)
    total_reports: int = Field(default=0)
    reports: List[BlufReportOutput] = Field(default_factory=list)
