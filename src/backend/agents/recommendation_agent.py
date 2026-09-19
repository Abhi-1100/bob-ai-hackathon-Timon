"""
LLM Recommendation Agent powered by Llama 3.3 70B via Groq.
Acts as a Senior SOC Analyst to generate grounded, actionable containment,
investigation, and remediation guidance for correlated attack chains.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq

from schemas.recommendation import RecommendationOutput

logger = logging.getLogger("recommendation_agent")

GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


class LLMRecommendationError(Exception):
    """Raised when the LLM recommendation agent fails."""
    pass


class RecommendationAgent:
    """
    Agent responsible for generating structured, SOC-grade security recommendations
    using Llama 3.3 70B via Groq with grounded context and Pydantic parsing.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model_name = GROQ_MODEL_NAME
        self.parser = PydanticOutputParser(pydantic_object=RecommendationOutput)
        self.llm = self._init_llm()

    def _init_llm(self) -> Optional[ChatGroq]:
        """Initialize the ChatGroq client if an API key is available."""
        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY is not set. RecommendationAgent will operate with "
                "intelligent threat-grounded fallback recommendations."
            )
            return None
        try:
            return ChatGroq(
                groq_api_key=self.api_key,
                model_name=self.model_name,
                temperature=0.2,
                max_tokens=1500,
                max_retries=2,
            )
        except Exception as exc:
            logger.error(f"Failed to initialize ChatGroq: {exc}")
            return None

    def build_system_prompt(self) -> str:
        """Construct the strict system prompt defining the analyst persona and JSON requirement."""
        return (
            "You are a Senior Cybersecurity Threat Analyst.\n"
            "Given attack chains, MITRE ATT&CK mappings and risk scores, generate actionable security recommendations.\n\n"
            "Focus on:\n"
            "1. Containment\n"
            "2. Investigation\n"
            "3. Recovery\n"
            "4. Future Prevention\n\n"
            "REQUIREMENTS:\n"
            "- Generate between 3 and 5 specific, actionable, cybersecurity-focused actions per category.\n"
            "- Avoid generic advice like 'be careful' or 'monitor systems'. Reference actual protocols, tools, commands, or firewall rules.\n"
            "- Return valid JSON only matching the requested schema.\n"
            "- NO markdown fences like ```json, NO preamble, and NO explanations outside the JSON object."
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
    ) -> str:
        """Construct the human prompt containing the full grounded context."""
        techniques_summary = [
            f"- {t.get('technique_id', 'Unknown')}: {t.get('name', 'Unknown')} (Tactic: {t.get('tactic', 'Unknown')})"
            for t in mitre_techniques
        ]
        techniques_str = "\n".join(techniques_summary) if techniques_summary else "None mapped"
        reasoning_str = "\n".join([f"- {r}" for r in reasoning]) if reasoning else "None specified"
        dest_str = ", ".join(destination_ips) if destination_ips else "Internal Network"

        prompt = f"""ATTACK CONTEXT:
Attack Chain ID: {chain_id}
Adversary Source IP: {source_ip}
Target Destination IP(s): {dest_str}
Observed Event Progression: {' -> '.join(events) if events else 'Unknown'}
Total Events in Chain: {len(events)}

MITRE ATT&CK MAPPINGS:
{techniques_str}

RISK EVALUATION:
Composite Risk Score: {risk_score} / 100
Severity Level: {risk_level}
Identified Risk Reasoning:
{reasoning_str}

OUTPUT FORMAT INSTRUCTIONS:
{self.parser.get_format_instructions()}

Generate the security recommendations in strict JSON now:"""
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
    ) -> RecommendationOutput:
        """
        Invoke Llama 3.3 70B via Groq to generate structured recommendations.
        Falls back to deterministic grounded recommendations if LLM/API is unavailable.
        """
        logger.info(f"Generating recommendations for chain {chain_id} via {self.model_name}")

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
        )

        if self.llm is None:
            logger.info("Using intelligent grounded rule-based generator (Groq LLM offline or key not provided)")
            return self._generate_grounded_fallback(
                chain_id=chain_id,
                events=events,
                source_ip=source_ip,
                destination_ips=destination_ips,
                mitre_techniques=mitre_techniques,
                risk_score=risk_score,
                risk_level=risk_level,
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        # Call LLM with up to 2 retry attempts for parsing
        last_error = None
        for attempt in range(1, 3):
            try:
                logger.info(f"Invoking Groq API for {chain_id} (attempt {attempt}/2)")
                response = self.llm.invoke(messages)
                raw_text = response.content if hasattr(response, "content") else str(response)
                return self.parse_and_validate(raw_text, chain_id)
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt} failed for chain {chain_id}: {exc}")

        logger.error(f"Groq generation failed after retries: {last_error}. Employing grounded fallback.")
        return self._generate_grounded_fallback(
            chain_id=chain_id,
            events=events,
            source_ip=source_ip,
            destination_ips=destination_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
        )

    def parse_and_validate(self, raw_text: str, chain_id: str) -> RecommendationOutput:
        """
        Clean, parse, and validate the LLM's JSON output using Pydantic.
        Strips markdown ticks, extracts JSON blocks, and validates item counts.
        """
        text = raw_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
            text = text.strip()

        # Extract JSON object using regex if surrounded by conversational filler
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as jde:
            raise LLMRecommendationError(f"Failed to parse LLM response as JSON: {jde}. Raw text: {raw_text[:200]}")

        # Ensure chain_id matches requested chain
        if not data.get("chain_id"):
            data["chain_id"] = chain_id

        # Validate with Pydantic model
        return RecommendationOutput.model_validate(data)

    def _generate_grounded_fallback(
        self,
        chain_id: str,
        events: List[str],
        source_ip: str,
        destination_ips: List[str],
        mitre_techniques: List[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
    ) -> RecommendationOutput:
        """
        Deterministic, threat-grounded recommendation generator.
        Produces specific, high-quality, actionable SOC recommendations tailored to
        the exact event types, IPs, and MITRE tactics observed in the chain.
        """
        dest_str = destination_ips[0] if destination_ips else "affected internal hosts"
        has_malware = any("malware" in e.lower() for e in events)
        has_cred = any("dumping" in e.lower() or "brute" in e.lower() for e in events)
        has_exfil = any("exfiltration" in e.lower() for e in events)
        has_cmd = any("command" in e.lower() or "powershell" in e.lower() for e in events)

        # 1. Immediate Actions (3-5 specific actions)
        immediate = [
            f"Add inbound/outbound deny rule on perimeter firewalls for source IP {source_ip}",
            f"Isolate primary targeted host ({dest_str}) from the local network segment via EDR or VLAN change",
            "Terminate active remote sessions and kill suspicious child processes spawned under cmd.exe/powershell.exe",
        ]
        if has_cred:
            immediate.append("Immediately revoke active Kerberos TGTs and trigger password resets for compromised accounts")
        elif has_exfil:
            immediate.append("Sever external network connections to confirmed unauthorized data staging destinations")
        else:
            immediate.append("Preserve volatile system memory (RAM dump) on affected endpoints for forensic triage")

        # 2. Containment Actions (3-5 actions)
        containment = [
            f"Enforce microsegmentation to block lateral SMB (445) and RDP (3389) traffic from {dest_str}",
            "Block identified file hashes and process binaries across all endpoints via EDR blocklist",
            "Temporarily restrict outbound internet access for the target subnet to approved proxy egress only",
        ]
        if has_malware:
            containment.append("Quarantine staging directories (e.g., %TEMP%, %APPDATA%) on infected endpoints")
        else:
            containment.append("Disable inactive or suspect service accounts associated with the intrusion activity")

        # 3. Investigation Actions (3-5 actions)
        investigation = [
            f"Query SIEM logs for all network connections originating from or directed to {source_ip} over the last 30 days",
            "Analyze PowerShell ScriptBlock logs (Event ID 4104) and Process Creation events (Event ID 4688)",
            "Review authentication failure and success logs (Event IDs 4624/4625) to map the scope of credential use",
        ]
        if has_malware:
            investigation.append("Submit suspected payload binaries to sandbox environment for static and dynamic analysis")
        else:
            investigation.append("Inspect Scheduled Tasks and registry Run keys for unauthorized persistence mechanisms")

        # 4. Prevention Actions (3-5 actions)
        prevention = [
            "Enable Windows Defender Credential Guard to protect LSASS memory against unauthorized dumping",
            "Mandate phishing-resistant Multi-Factor Authentication (FIDO2) on all administrative and remote access portals",
            "Audit and restrict local administrative privileges using Microsoft LAPS across all workstations and servers",
            "Update IPS and Snort/Suricata signatures with indicators of compromise identified in this intrusion",
        ]

        # 5. Executive Summary
        techniques_list = [t.get("name", "") for t in mitre_techniques if t.get("name")]
        techniques_phrase = f" leveraging {', '.join(techniques_list[:2])}" if techniques_list else ""
        executive_summary = (
            f"A {risk_level}-severity intrusion ({risk_score}/100) was detected against {dest_str} "
            f"originating from {source_ip}{techniques_phrase}. Immediate network containment, "
            f"credential revocation, and endpoint triage are enacted to eliminate persistence and mitigate exposure."
        )

        return RecommendationOutput(
            chain_id=chain_id,
            immediate_actions=immediate,
            containment_actions=containment,
            investigation_actions=investigation,
            prevention_actions=prevention,
            executive_summary=executive_summary,
        )
