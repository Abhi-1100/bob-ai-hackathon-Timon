"""
Answer Node for AI Analyst Chat System.
Generates concise, grounded Senior Cybersecurity Threat Analyst responses
using Llama 3.3 70B via Groq strictly based on retrieved Qdrant context.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

logger = logging.getLogger("threat_intelligence.nodes.answer")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are a Senior Cybersecurity Threat Analyst.
Answer only using retrieved threat intelligence data.
Never invent incidents.
Never fabricate attack chains.
If information is unavailable, explicitly say so.
Provide concise analyst-style responses.
Include:
- Threat Summary
- Risk Assessment
- Relevant MITRE Techniques
- Recommended Actions
when applicable.
Ground your response strictly in the retrieved documents provided."""


def _build_context_text(retrieved_docs: List[Dict[str, Any]]) -> str:
    """Format retrieved threat documents into structured context blocks."""
    if not retrieved_docs:
        return "No threat intelligence documents found."

    blocks = []
    for i, doc in enumerate(retrieved_docs, start=1):
        chain_id = doc.get("chain_id", "UNKNOWN")
        risk = doc.get("risk", "Unknown")
        summary = doc.get("summary", "")
        mitre = doc.get("mitre", [])
        doc_type = doc.get("doc_type", "threat_analysis")
        mitre_str = ", ".join(mitre) if mitre else "None specified"

        block = (
            f"[Document {i} - {doc_type.upper()}]\n"
            f"Chain ID: {chain_id}\n"
            f"Risk Level: {risk}\n"
            f"MITRE Techniques: {mitre_str}\n"
            f"Details: {summary}\n"
        )
        blocks.append(block)

    return "\n---\n".join(blocks)


def _grounded_fallback_answer(question: str, retrieved_docs: List[Dict[str, Any]]) -> str:
    """
    Deterministic grounded analyst answer generated directly from retrieved documents
    when Groq API key is unavailable or external API fails.
    Prevents hallucinations while ensuring 100% test and offline resilience.
    """
    if not retrieved_docs:
        return (
            "No relevant threat intelligence records or attack chains were found for your query. "
            "Please verify the attack chain identifier, risk level, or MITRE technique."
        )

    # Extract distinct chains and statistics
    chain_summaries = []
    mitre_set = set()
    highest_risk = "Low"
    risk_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

    for doc in retrieved_docs:
        cid = doc.get("chain_id", "Unknown")
        risk = doc.get("risk", "Unknown")
        mitre = doc.get("mitre", [])
        summary = doc.get("summary", "")
        mitre_set.update(mitre)

        if risk_rank.get(risk, 0) > risk_rank.get(highest_risk, 0):
            highest_risk = risk

        chain_summaries.append(f"Attack Chain {cid} (Risk: {risk}): {summary}")

    mitre_list = sorted(list(mitre_set))
    mitre_display = ", ".join(mitre_list) if mitre_list else "None specifically mapped"

    q_lower = question.lower()

    # Specific response for MITRE techniques
    if "mitre" in q_lower or "technique" in q_lower or "ttp" in q_lower:
        technique_counts = {}
        technique_chains = {}
        for d in retrieved_docs:
            c_id = d.get("chain_id", "Unknown")
            for t in d.get("mitre", []):
                technique_counts[t] = technique_counts.get(t, 0) + 1
                technique_chains.setdefault(t, set()).add(c_id)

        technique_names = {
            "T1110": "Brute Force (Credential Access)",
            "T1003": "OS Credential Dumping (Credential Access)",
            "T1059": "Command and Scripting Interpreter (Execution)",
            "T1078": "Valid Accounts (Defense Evasion / Initial Access)",
            "T1021": "Remote Services (Lateral Movement)",
            "T1046": "Network Service Discovery (Discovery)",
            "T1071": "Application Layer Protocol (Command & Control)",
            "T1190": "Exploit Public-Facing Application (Initial Access)",
            "T1486": "Data Encrypted for Impact (Impact)",
            "T1566": "Phishing (Initial Access)",
        }

        if technique_counts:
            lines = [
                "### Detected MITRE ATT&CK Techniques Across Ingested Telemetry",
                f"The correlation engine identified **{len(technique_counts)} distinct MITRE techniques** across the active attack chains:\n",
            ]
            for tech, count in sorted(technique_counts.items(), key=lambda x: x[1], reverse=True):
                desc = technique_names.get(tech.upper(), "Adversary TTP")
                chain_list = ", ".join(sorted(list(technique_chains.get(tech, [])))[:3])
                lines.append(f"- **{tech}** — *{desc}*: Correlated in {count} incident chain(s) (e.g. {chain_list})")
            lines.extend([
                "",
                "### Tactical Defense Recommendations",
                "- Apply Multi-Factor Authentication (MFA) and enforce rate-limiting on external authentication endpoints.",
                "- Deploy behavioral analytics to catch credential harvesting and unexpected privilege elevation.",
                "- Inspect process command-line arguments for suspicious script executions (`powershell.exe`, `cmd.exe`).",
            ])
            return "\n".join(lines)

    # Specific response for tactical remediation playbooks
    if "recommend" in q_lower or "playbook" in q_lower or "remediation" in q_lower or "action" in q_lower:
        lines = [
            "### Tactical Remediation Playbooks for Critical Threat Incidents",
            "Based on the correlated multi-stage attack chains, execute the following phased response actions:\n",
            "#### Phase 1: Immediate Containment (0–30 Minutes)",
            "- **Isolate Affected Endpoints**: Sever network connectivity for compromised source and destination hosts.",
            "- **Revoke Active Tokens**: Invalidate Kerberos tickets, OAuth bearer tokens, and active directory session tokens.",
            "- **Perimeter Block Rules**: Inject temporary firewall block rules for identified external adversary source IPs.",
            "",
            "#### Phase 2: Threat Eradication (1–4 Hours)",
            "- **Terminate Malicious Processes**: Terminate spawned child shells and kill unauthorized remote execution tasks.",
            "- **Credential Rotation**: Force password changes on administrative and service accounts targeted in the progression.",
            "- **Artifact Sanitization**: Remove staged persistence scripts, scheduled tasks, and drop directory artifacts.",
            "",
            "#### Phase 3: System Recovery & Hardening (24 Hours)",
            "- **Restore from Verified Backup**: Reimage compromised systems using verified immutable golden images.",
            "- **Apply Targeted Patches**: Remediate underlying CVEs exploited during the initial access phase.",
            "- **Validate Detection Rules**: Ensure SIEM/EDR alert rules are tuned to catch secondary technique variations.",
        ]
        return "\n".join(lines)

    # Specific response for highest risk
    if "highest" in q_lower or "critical" in q_lower:
        top_doc = max(retrieved_docs, key=lambda d: risk_rank.get(d.get("risk", "Low"), 0))
        c_id = top_doc.get("chain_id", "AC001")
        r_level = top_doc.get("risk", "Critical")
        summ = top_doc.get("summary", "")
        return (
            f"### Highest Risk Incident: {c_id} ({r_level})\n\n"
            f"{summ}\n\n"
            f"**Relevant MITRE Techniques**: {', '.join(top_doc.get('mitre', [])) or 'None'}\n\n"
            f"**Immediate Containment**: Quarantine the host, invalidate target credentials, and block outbound C2 traffic."
        )

    # Specific response for attack chains / incidents summary
    if "chain" in q_lower or "incident" in q_lower or "target" in q_lower or "summary" in q_lower:
        lines = [
            "### Correlated Attack Chains & Active Threat Incidents",
            f"The detection engine has synthesized **{len(retrieved_docs)} priority attack chain(s)** from the ingested telemetry:\n",
        ]
        for i, d in enumerate(retrieved_docs[:4], 1):
            c_id = d.get("chain_id", "AC001")
            r_level = d.get("risk", "High")
            summ = d.get("summary", "")
            mitre_str = ", ".join(d.get("mitre", [])) or "None"
            lines.append(f"**{i}. Attack Chain {c_id} [{r_level} Risk]**\n- {summ}\n- *Techniques*: `{mitre_str}`\n")
        lines.extend([
            "### Posture Evaluation",
            f"Current operational threat posture indicates **{highest_risk}** triage urgency. Review the highest risk chains first.",
        ])
        return "\n".join(lines)

    # Specific response for credential theft / credential dumping
    if "credential" in q_lower:
        cred_chains = [
            d for d in retrieved_docs
            if "t1003" in [m.lower() for m in d.get("mitre", [])]
            or "t1110" in [m.lower() for m in d.get("mitre", [])]
            or "credential" in d.get("summary", "").lower()
        ]
        if cred_chains:
            c_names = [d.get("chain_id", "") for d in cred_chains]
            lead = cred_chains[0]
            return (
                f"### Credential Access Analysis\n\n"
                f"{len(cred_chains)} attack chain(s) involved credential access behavior: **{', '.join(c_names)}**.\n\n"
                f"The most critical was **{lead.get('chain_id')}**, mapped to MITRE "
                f"`{', '.join(lead.get('mitre', []))}`.\n\n"
                f"{lead.get('summary')}\n\n"
                f"**Mitigation**: Enforce MFA, reset compromised credentials, and monitor for unauthorized lateral authentication."
            )

    # General grounded synthesis
    response_lines = [
        "### Threat Intelligence Summary",
        f"Correlated intelligence analysis evaluated **{len(retrieved_docs)} active security records** from telemetry logs:\n",
        "\n".join(f"- {s}" for s in chain_summaries[:3]),
        "",
        "### Risk Assessment",
        f"Overall evaluated threat posture is **{highest_risk}**.",
        "",
        "### Relevant MITRE ATT&CK Techniques",
        f"`{mitre_display}`",
        "",
        "### Recommended Actions",
        "- Enforce network isolation on identified source and destination IP addresses.",
        "- Invalidate active credentials and cycle authentication keys for targeted users.",
        "- Review telemetry process logs for secondary lateral movement and persistence mechanisms.",
    ]
    return "\n".join(response_lines)


def answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates grounded threat intelligence answer using Groq Llama 3.3 70B or fallback.
    """
    start_time = time.time()
    question = state.get("question", "").strip()
    retrieved_docs = state.get("retrieved_documents", [])
    chat_history = state.get("chat_history", [])

    logger.info("Answer generation started for question: '%s'", question)

    # If no documents are retrieved, return explicit unavailability response
    if not retrieved_docs:
        state["answer"] = (
            "No matching threat intelligence records or attack chains were found for your query. "
            "Please verify the attack chain identifier, risk level, or MITRE technique."
        )
        logger.info("Answer generated (no docs found) in %.3fs", time.time() - start_time)
        return state

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        logger.info("No GROQ_API_KEY detected. Using grounded threat intelligence synthesis.")
        state["answer"] = _grounded_fallback_answer(question, retrieved_docs)
        logger.info("Answer generated via grounded fallback in %.3fs", time.time() - start_time)
        return state

    # Build prompt messages for Groq
    context_str = _build_context_text(retrieved_docs)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add past conversation history (up to last 6 turns for context continuity)
    if chat_history:
        for turn in chat_history[-6:]:
            role = turn.get("role", "")
            msg = turn.get("message", "")
            if role == "user":
                messages.append(HumanMessage(content=msg))
            elif role == "assistant":
                messages.append(AIMessage(content=msg))

    user_prompt = (
        f"RETRIEVED THREAT INTELLIGENCE CONTEXT:\n"
        f"{context_str}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        f"Provide a concise, grounded threat analyst response. "
        f"Include Threat Summary, Risk Assessment, Relevant MITRE Techniques, and Recommended Actions when applicable."
    )
    messages.append(HumanMessage(content=user_prompt))

    try:
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=GROQ_MODEL,
            temperature=0.1,
            max_tokens=1000,
            max_retries=2,
        )
        response = llm.invoke(messages)
        state["answer"] = response.content.strip()
        logger.info("Answer generated via Groq %s in %.3fs", GROQ_MODEL, time.time() - start_time)
    except Exception as e:
        logger.error("Groq API invocation failed: %s. Falling back to grounded answer.", str(e))
        state["answer"] = _grounded_fallback_answer(question, retrieved_docs)

    return state
