"""
BLUF Report Generation Agent powered by Llama 3.3 70B via Groq.
Acts as a Senior Cyber Threat Intelligence Analyst to synthesize attack chains,
MITRE techniques, risk scores, and recommendations into concise, commander-ready
Bottom Line Up Front (BLUF) intelligence reports.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq

from schemas.report import BlufReportOutput

logger = logging.getLogger("bluf_report_agent")

GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


class BlufReportError(Exception):
    """Raised when the BLUF report generation fails."""
    pass


class BlufReportAgent:
    """
    Agent responsible for generating structured, executive-ready BLUF reports
    using Llama 3.3 70B via Groq with grounded context and Pydantic parsing.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model_name = GROQ_MODEL_NAME
        self.parser = PydanticOutputParser(pydantic_object=BlufReportOutput)
        self.llm = self._init_llm()

    def _init_llm(self) -> Optional[ChatGroq]:
        """Initialize the ChatGroq client if an API key is available."""
        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY is not set. BlufReportAgent will operate with "
                "intelligent threat-grounded fallback report generation."
            )
            return None
        try:
            return ChatGroq(
                groq_api_key=self.api_key,
                model_name=self.model_name,
                temperature=0.2,
                max_tokens=2000,
                max_retries=2,
            )
        except Exception as exc:
            logger.error(f"Failed to initialize ChatGroq for BLUF agent: {exc}")
            return None

    def build_system_prompt(self) -> str:
        """Construct the system prompt defining the analyst persona and strict constraints."""
        return (
            "You are a Senior Cyber Threat Intelligence Analyst.\n"
            "Generate concise executive-ready BLUF reports.\n\n"
            "Focus on:\n"
            "- Threat Summary\n"
            "- Business Impact\n"
            "- Risk Assessment\n"
            "- Recommended Actions\n\n"
            "GUIDELINES:\n"
            "- Use professional cybersecurity language.\n"
            "- Avoid speculation. Ground every statement in the provided attack chain, MITRE mappings and risk score.\n"
            "- The executive_summary MUST be under 100 words and answer: What happened? Why it matters? What should be done?\n"
            "- Return JSON only.\n"
            "- NO markdown.\n"
            "- NO code blocks.\n"
            "- NO hallucinated data."
        )

    def build_human_prompt(
        self,
        chain_id: str,
        events: List[str],
        source_ip: str,
        destination_ips: List[str],
        mitre_techniques: List[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
        reasoning: List[str],
        recommendations: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Construct the human prompt containing the full grounded context."""
        techniques_str = "\n".join([
            f"- {t.get('technique_id', 'Unknown')}: {t.get('name', 'Unknown')} (Tactic: {t.get('tactic', 'Unknown')})"
            for t in mitre_techniques
        ]) if mitre_techniques else "None mapped"

        reasoning_str = "\n".join([f"- {r}" for r in reasoning]) if reasoning else "None specified"
        dest_str = ", ".join(destination_ips) if destination_ips else "Internal Network"

        rec_actions = []
        if recommendations:
            imm = recommendations.get("immediate_actions", [])
            cont = recommendations.get("containment_actions", [])
            if imm:
                rec_actions.extend([f"Immediate: {a}" for a in imm[:2]])
            if cont:
                rec_actions.extend([f"Containment: {a}" for a in cont[:2]])
        rec_str = "\n".join([f"- {a}" for a in rec_actions]) if rec_actions else "Standard incident response protocol"

        prompt = f"""THREAT INTELLIGENCE CONTEXT:
Attack Chain ID: {chain_id}
Adversary Source IP: {source_ip}
Targeted Asset(s): {dest_str}
Observed Progression: {' -> '.join(events) if events else 'Unknown'}
Total Events: {len(events)}

MITRE ATT&CK TECHNIQUES:
{techniques_str}

RISK EVALUATION:
Score: {risk_score} / 100
Threat Level: {risk_level}
Identified Risk Reasoning:
{reasoning_str}

KEY ACTIONABLE RECOMMENDATIONS:
{rec_str}

OUTPUT FORMAT INSTRUCTIONS:
{self.parser.get_format_instructions()}

Generate the structured BLUF report in valid JSON now:"""
        return prompt

    def generate(
        self,
        chain_id: str,
        events: List[str],
        source_ip: str,
        destination_ips: List[str],
        mitre_techniques: List[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
        reasoning: List[str],
        recommendations: Optional[Dict[str, Any]] = None,
    ) -> BlufReportOutput:
        """
        Invoke Llama 3.3 70B via Groq to generate executive BLUF intelligence report.
        Falls back to threat-grounded generation if LLM or API key is unavailable.
        """
        logger.info(f"Generating BLUF report for chain {chain_id} via {self.model_name}")

        system_prompt = self.build_system_prompt()
        human_prompt = self.build_human_prompt(
            chain_id=chain_id,
            events=events,
            source_ip=source_ip,
            destination_ips=destination_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
            reasoning=reasoning,
            recommendations=recommendations,
        )

        if self.llm is None:
            logger.info("Using intelligent threat-grounded BLUF report generator (Groq LLM offline or key not set)")
            return self._generate_grounded_fallback(
                chain_id=chain_id,
                events=events,
                source_ip=source_ip,
                destination_ips=destination_ips,
                mitre_techniques=mitre_techniques,
                risk_score=risk_score,
                risk_level=risk_level,
                reasoning=reasoning,
                recommendations=recommendations,
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        last_error = None
        for attempt in range(1, 3):
            try:
                logger.info(f"Invoking Groq API for BLUF report {chain_id} (attempt {attempt}/2)")
                response = self.llm.invoke(messages)
                raw_text = response.content if hasattr(response, "content") else str(response)
                return self.parse_and_validate(raw_text, chain_id, risk_level)
            except Exception as exc:
                last_error = exc
                logger.warning(f"BLUF generation attempt {attempt} failed for {chain_id}: {exc}")

        logger.error(f"Groq BLUF generation failed after retries: {last_error}. Employing grounded fallback.")
        return self._generate_grounded_fallback(
            chain_id=chain_id,
            events=events,
            source_ip=source_ip,
            destination_ips=destination_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
            reasoning=reasoning,
            recommendations=recommendations,
        )

    def parse_and_validate(
        self, raw_text: str, chain_id: str, default_threat_level: str
    ) -> BlufReportOutput:
        """
        Clean, parse, and validate the LLM's JSON output using Pydantic.
        Strips markdown ticks, extracts JSON blocks, and verifies required fields.
        """
        text = raw_text.strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
            text = text.strip()

        # Extract JSON substring using regex if conversational wrapper exists
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as jde:
            raise BlufReportError(f"Failed to parse LLM BLUF response as JSON: {jde}. Raw text: {raw_text[:200]}")

        # Ensure chain_id and threat_level are populated
        if not data.get("chain_id"):
            data["chain_id"] = chain_id
        if not data.get("threat_level"):
            data["threat_level"] = default_threat_level

        return BlufReportOutput.model_validate(data)

    def _generate_grounded_fallback(
        self,
        chain_id: str,
        events: List[str],
        source_ip: str,
        destination_ips: List[str],
        mitre_techniques: List[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
        reasoning: List[str],
        recommendations: Optional[Dict[str, Any]] = None,
    ) -> BlufReportOutput:
        """
        Deterministic, threat-grounded BLUF report generator.
        Produces a high-quality, professional executive report tailored strictly to the
        provided attack chain progression, MITRE mappings, risk score, and recommendations.
        """
        target_str = ", ".join(destination_ips) if destination_ips else "internal enterprise assets"
        progression_str = " -> ".join(events) if events else "Suspicious Activity"

        # 1. Executive Summary (<100 words answering What happened, Why it matters, What should be done)
        exec_summary = (
            f"An active multi-stage intrusion was detected targeting {target_str} originating from adversary IP {source_ip}. "
            f"The adversary progressed through {len(events)} stages ({progression_str}), presenting a verified {risk_level} operational threat. "
            f"Immediate network containment of affected endpoints and edge firewall blocking are actively enforced to prevent lateral compromise."
        )

        # 2. Attack Overview
        attack_overview = (
            f"Chronological activity initiated with reconnaissance and initial access attempts from {source_ip}, "
            f"subsequently progressing across observed behaviors: {progression_str}. "
            f"The rapid escalation across {len(events)} correlated alerts demonstrates a purposeful attack sequence aimed at host exploitation."
        )

        # 3. Affected Assets
        affected_assets = (
            f"Primary Target(s): {target_str}\n"
            f"External Adversary Source IP: {source_ip}\n"
            f"Scope of Impact: Restricted to targeted host subnet pending active lateral movement investigation."
        )

        # 4. MITRE Summary
        if mitre_techniques:
            tech_lines = [
                f"- {t.get('technique_id')}: {t.get('name')} ({t.get('tactic', 'Tactic Unknown')})"
                for t in mitre_techniques
            ]
            mitre_summary = (
                f"Observed activities correlate to {len(mitre_techniques)} verified MITRE ATT&CK technique(s):\n"
                + "\n".join(tech_lines)
                + "\nThese techniques align with adversary objectives for initial compromise and credential acquisition."
            )
        else:
            mitre_summary = "Adversary tactics indicate pre-attack probing and initial access staging."

        # 5. Risk Assessment
        reasons_text = "; ".join(reasoning) if reasoning else "Observed multi-stage progression"
        risk_assessment = (
            f"Assessed Risk Score: {risk_score}/100 ({risk_level}). "
            f"This severity classification reflects: {reasons_text}. "
            f"Potential business impact includes credential exposure, unauthorized host control, and data disruption."
        )

        # 6. Recommended Actions
        actions_list = []
        if recommendations:
            imm = recommendations.get("immediate_actions", [])
            cont = recommendations.get("containment_actions", [])
            for action in imm[:2]:
                actions_list.append(f"• [Immediate] {action}")
            for action in cont[:2]:
                actions_list.append(f"• [Containment] {action}")
        if not actions_list:
            actions_list = [
                f"• [Immediate] Block adversary source IP {source_ip} at edge firewalls.",
                f"• [Immediate] Isolate target host(s) {target_str} from corporate subnet.",
                "• [Containment] Terminate suspect remote sessions and revoke active Kerberos tokens.",
                "• [Investigation] Acquire forensic memory dump for timeline reconstruction.",
            ]
        recommended_actions = "\n".join(actions_list)

        # 7. Conclusion
        conclusion = (
            f"The intrusion represents an escalated {risk_level} threat requiring priority operational handling. "
            f"Next recommended milestone: Complete forensic memory triage on {target_str} and verify full eradication of adversary footholds."
        )

        return BlufReportOutput(
            chain_id=chain_id,
            threat_level=risk_level,
            executive_summary=exec_summary,
            attack_overview=attack_overview,
            affected_assets=affected_assets,
            mitre_summary=mitre_summary,
            risk_assessment=risk_assessment,
            recommended_actions=recommended_actions,
            conclusion=conclusion,
        )
