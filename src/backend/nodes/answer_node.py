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

SYSTEM_PROMPT = """You are a Senior Cybersecurity Threat Analyst assistant for the SOC platform.
If the user provides a greeting, casual conversation, or asks about your capabilities (e.g., 'hi', 'hello', 'who are you', 'how can you help'), respond politely and professionally as a SOC assistant and explain how you can help investigate threat telemetry.
For security questions, answer only using retrieved threat intelligence data.
Never invent incidents or fabricate attack chains that are not present in the data.
If specific information is unavailable in the retrieved data, explicitly state so.
Provide clear, structured analyst responses with Threat Summary, Risk Assessment, MITRE Techniques, and Recommended Actions when applicable."""


def _get_groq_candidates() -> List[str]:
    configured = os.getenv("GROQ_MODEL", "").strip('"\' ')
    defaults = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    if configured:
        return [configured] + [m for m in defaults if m != configured]
    return defaults


def _is_greeting(q: str) -> bool:
    """Check if the user message is a greeting or introductory query."""
    q_clean = q.lower().strip().strip("!?,.")
    greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning",
        "good afternoon", "good evening", "howdy", "sup", "yo", "namaste"
    }
    if q_clean in greetings:
        return True
    if any(q_clean.startswith(g + " ") for g in greetings):
        return True
    if q_clean in {"who are you", "what are you", "what can you do", "help", "how can you help", "can you help me"}:
        return True
    return False


def _greeting_response() -> str:
    """Friendly greeting explaining the assistant's capabilities."""
    return (
        "Hello! I am your **AI Threat Intelligence & SOC Analyst Assistant**.\n\n"
        "I can assist you with your security investigations and telemetry analysis:\n"
        "- **Correlated Attack Chains**: Analyze multi-stage kill-chains and identify high-risk attacker progressions.\n"
        "- **MITRE ATT&CK Mapping**: Identify tactics, techniques, and adversary TTPs observed across alerts.\n"
        "- **Risk Prioritization**: Assess prioritized threats across critical enterprise destinations and source IPs.\n"
        "- **Behavioral Anomaly Analysis**: Investigate off-hours activity, velocity bursts, and baseline deviations.\n"
        "- **Incident Remediation Playbooks**: Provide immediate containment and eradication protocols.\n\n"
        "How can I help with your investigation? You can ask about any incident (e.g. *'Summarize attack chain AC181'*), top targeted assets, or active threats."
    )



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
    if _is_greeting(question):
        return _greeting_response()

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

    # 1. Specific ordinal priority request ("second error", "second alert", "2nd priority", "third", "rank 2", etc.)
    ordinal_map = {
        "first": 0, "1st": 0, "top": 0, "highest": 0, "rank 1": 0, "#1": 0,
        "second": 1, "2nd": 1, "rank 2": 1, "#2": 1,
        "third": 2, "3rd": 2, "rank 3": 2, "#3": 2,
        "fourth": 3, "4th": 3, "rank 4": 3, "#4": 3,
        "fifth": 4, "5th": 4, "rank 5": 4, "#5": 4,
    }
    target_idx = None
    ordinal_label = None
    for word, idx in ordinal_map.items():
        if word in q_lower:
            target_idx = idx
            ordinal_label = word.capitalize()
            break

    if target_idx is not None and target_idx > 0:
        if target_idx < len(retrieved_docs):
            doc = retrieved_docs[target_idx]
            cid = doc.get("chain_id", f"Chain #{target_idx+1}")
            risk = doc.get("risk", "High")
            summ = doc.get("summary", "")
            mitre_str = ", ".join(doc.get("mitre", [])) or "None specifically mapped"
            meta = doc.get("metadata", {})
            src_ip = meta.get("source_ip") or doc.get("source_ip", "Unknown")
            dst_ips = meta.get("destination_ips") or doc.get("destination_ips", "Internal Assets")
            alert_cnt = meta.get("alert_count") or doc.get("alert_count", "Multiple")
            
            return (
                f"### {ordinal_label} Priority Incident: Attack Chain {cid} [{risk} Risk]\n\n"
                f"- **Chain ID**: `{cid}`\n"
                f"- **Assessed Severity**: **{risk}**\n"
                f"- **Adversary Source IP**: `{src_ip}`\n"
                f"- **Targeted Destination Assets**: `{dst_ips}`\n"
                f"- **Total Correlated Alerts**: {alert_cnt} events\n"
                f"- **Mapped MITRE Techniques**: `{mitre_str}`\n\n"
                f"#### Progression Summary\n{summ}\n\n"
                f"#### Immediate Action Protocol\n"
                f"- Quarantine `{src_ip}` on perimeter ingress filters.\n"
                f"- Audit process creation logs on `{dst_ips}` for unauthorized execution attempts."
            )
        else:
            return (
                f"The correlation engine evaluated {len(retrieved_docs)} active priority chains. "
                f"No record at rank #{target_idx+1} was found in the current filtered telemetry."
            )

    # 2. Destination Assets and IP addresses query ("destination", "asset", "ip address", "under active attack", "targets")
    if any(k in q_lower for k in ["destination", "asset", "ip address", "under active attack", "under attack", "targeted host", "victim", "impacted", "which host", "which ip", "what ip"]):
        dest_map = {}
        src_map = {}
        import re
        for d in retrieved_docs:
            cid = d.get("chain_id", "")
            risk = d.get("risk", "Medium")
            meta = d.get("metadata", {})
            dst = meta.get("destination_ips") or d.get("destination_ips") or ""
            src = meta.get("source_ip") or d.get("source_ip") or ""
            
            if not dst and "targeting destination assets" in d.get("summary", ""):
                m_dst = re.search(r"targeting destination assets \[([^\]]+)\]", d.get("summary", ""))
                if m_dst:
                    dst = m_dst.group(1)
            if not src and "source IP" in d.get("summary", ""):
                m_src = re.search(r"source IP ([^\s]+)", d.get("summary", ""))
                if m_src:
                    src = m_src.group(1)

            if dst:
                for ip in [i.strip() for i in dst.split(",") if i.strip()]:
                    dest_map.setdefault(ip, []).append(f"{cid} ({risk})")
            if src:
                src_map.setdefault(src, []).append(cid)

        lines = [
            "### Destination Assets & IP Addresses Under Active Attack",
            f"Correlation analysis identified **{len(dest_map)} critical internal destination assets** actively targeted across telemetry:\n",
            "#### Impacted Destination Assets (Targets)",
        ]
        for ip, chains in dest_map.items():
            lines.append(f"- **`{ip}`**: Targeted by attack chain(s) **{', '.join(chains)}**")
        
        if src_map:
            lines.append("\n#### Identified Adversary Origin IPs (Sources)")
            for ip, chains in src_map.items():
                lines.append(f"- **`{ip}`**: Originating source for chain(s) **{', '.join(chains)}**")

        lines.extend([
            "",
            "#### Immediate Containment Protocol",
            "1. **Isolate Target Hosts**: Temporarily partition impacted destination assets from sensitive VLANs.",
            "2. **Block Adversary Sources**: Apply egress/ingress firewall drops against identified source IPs.",
            "3. **Credential Cycling**: Reset access tokens and authentication credentials for affected servers.",
        ])
        return "\n".join(lines)

    # 3. Behavioral & Anomaly queries
    if any(k in q_lower for k in ["behavior", "anomaly", "velocity", "baseline", "unusual", "novel"]):
        lines = [
            "### Behavioral & Contextual Anomaly Assessment",
            "The Behavioral Analysis Engine evaluates activity across 8 dimensions (Network Baseline, Velocity, Target Assets, Temporal Patterns, Entity Relations, Historical Baseline, Identity, and Device):\n",
        ]
        for d in retrieved_docs[:3]:
            cid = d.get("chain_id", "AC001")
            risk = d.get("risk", "High")
            summ = d.get("summary", "")
            lines.append(f"**Attack Chain {cid} [{risk} Priority]**:")
            lines.append(f"- {summ}")
        lines.extend([
            "",
            "### Key Contributing Behavioral Indicators",
            "- **High-Velocity Bursting**: Rapid event grouping exceeding established baseline intervals.",
            "- **First-Seen Entity Access**: External IPs communicating with internal hosts without prior historical baseline.",
            "- **Temporal Off-Hours Shifts**: Critical operations initiated outside standard operational business hours.",
        ])
        return "\n".join(lines)

    # 4. Specific response for attack events / error progression ("error", "alert", "alter", "event", "progression", "sequence")
    if any(k in q_lower for k in ["error", "alert", "alter", "event", "progression", "sequence", "what happened"]):
        lines = [
            "### Correlated Security Events & Alert Progression",
            f"The telemetry correlation engine processed alerts across **{len(retrieved_docs)} attack chain(s)**:\n",
        ]
        for i, d in enumerate(retrieved_docs[:4], start=1):
            cid = d.get("chain_id", "AC001")
            risk = d.get("risk", "High")
            summ = d.get("summary", "")
            mitre_str = ", ".join(d.get("mitre", [])) or "None"
            
            prog = "Security Event Sequence"
            if "Progression sequence:" in summ:
                prog_part = summ.split("Progression sequence:")[1].split(".")[0].strip()
                prog = f"Kill-Chain: `{prog_part}`"
            
            lines.append(f"**{i}. Attack Chain {cid} [{risk} Priority]**")
            lines.append(f"- {prog}")
            lines.append(f"- MITRE Techniques: `{mitre_str}`")
            lines.append(f"- Details: {summ.split('Progression sequence:')[0].strip()}\n")

        lines.extend([
            "### SOC Analyst Guidance",
            "- Triage critical kill-chain stages (`CommandExecution`, `DataTransfer`, `Malware`) first.",
            "- Check endpoint EDR telemetry for shell spawn arguments and outbound connection sockets.",
        ])
        return "\n".join(lines)

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

    # 1. Immediate greeting check: provide warm, helpful analyst orientation
    if _is_greeting(question):
        state["answer"] = _greeting_response()
        logger.info("Answered conversational greeting in %.3fs", time.time() - start_time)
        return state

    # If no documents are retrieved, return explicit unavailability response
    if not retrieved_docs:
        state["answer"] = (
            "No matching threat intelligence records or attack chains were found for your query. "
            "Please verify the attack chain identifier, risk level, or MITRE technique."
        )
        logger.info("Answer generated (no docs found) in %.3fs", time.time() - start_time)
        return state

    raw_api_key = os.getenv("GROQ_API_KEY", "")
    api_key = raw_api_key.strip('"\' ')

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

    last_error = None
    for model_name in _get_groq_candidates():
        try:
            llm = ChatGroq(
                groq_api_key=api_key,
                model_name=model_name,
                temperature=0.1,
                max_tokens=2500,
                max_retries=1,
            )
            response = llm.invoke(messages)
            state["answer"] = response.content.strip()
            logger.info("Answer generated via Groq %s in %.3fs", model_name, time.time() - start_time)
            return state
        except Exception as e:
            last_error = e
            logger.warning("Groq model %s failed: %s. Trying next candidate...", model_name, e)

    logger.error("All Groq model candidates failed (%s). Falling back to grounded answer.", last_error)
    state["answer"] = _grounded_fallback_answer(question, retrieved_docs)

    return state
