# 🛡️ TimonTrack — 5-Step Pipeline Deep Dive

> **Comprehensive Technical Guide:** How TimonTrack ingests raw security telemetry, reconstructs multi-stage attack chains, maps adversary behaviors to MITRE ATT&CK®, computes deterministic risk scores, and generates executive BLUF briefings and tactical playbooks.

---

## 🗺️ High-Level Pipeline Architecture

```
[Raw Security Alerts / CSV Feed]
                │
                ▼
  ┌──────────────────────────────────────────────┐
  │  Step 1: Ingestion & Normalization           │
  │  • Schema validation & regex sanitization    │
  │  • Canonical event naming dictionary         │
  │  • Multi-tenant user isolation               │
  └──────────────────────────────────────────────┘
                │
                ▼
  ┌──────────────────────────────────────────────┐
  │  Step 2: Alert Correlation Engine            │
  │  • Source-IP affinity & 30-min window        │
  │  • Chronological Attack Chain synthesis      │
  │  • Kill-chain progression sorting            │
  └──────────────────────────────────────────────┘
                │
                ▼
  ┌──────────────────────────────────────────────┐
  │  Step 3: Automated MITRE ATT&CK® Mapping     │
  │  • Deterministic knowledge-base lookup       │
  │  • Technique IDs (T1595, T1110, T1048, etc.) │
  │  • Tactic alignment & ATT&CK matrix coverage │
  └──────────────────────────────────────────────┘
                │
                ▼
  ┌──────────────────────────────────────────────┐
  │  Step 4: Deterministic Risk Scoring Engine   │
  │  • Zero-hallucination mathematical formula   │
  │  • Event weights + MITRE tactic bonus        │
  │  • Severity tiers (Low, Med, High, Critical) │
  └──────────────────────────────────────────────┘
                │
                ▼
  ┌──────────────────────────────────────────────┐
  │  Step 5: AI Synthesis & Playbook Generation  │
  │  • BLUF Executive Briefing (CISO ready)      │
  │  • 4-tier Tactical Containment Playbook      │
  │  • FastEmbed (384d) + Qdrant Vector Sync     │
  └──────────────────────────────────────────────┘
```

---

## 🔹 Step 1: Ingestion & Normalization

* **Source File:** [`src/backend/services/csv_parser.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/services/csv_parser.py)
* **Component:** `CSVParser` / Pydantic `Alert` Schema

### 1. The Challenge
Real-world enterprise environments ingest telemetry from dozens of disparate sensors (firewalls, anti-malware, EDR, cloud gateways). These tools produce inconsistent schemas, arbitrary naming conventions (e.g., `port scan`, `port_scan`, `portscan`, `sqli`), irregular timestamp formats, and missing metadata.

### 2. How It Operates
1. **Schema & Header Verification:** Checks for essential headers:
   * `timestamp`: Date and time of incident occurrence.
   * `src_ip`: Source IP address of the potential attacker.
   * `dst_ip`: Target host or internal resource IP address.
   * `event`: Security event name or alert type.
   * `severity`: Sensor-assigned severity rating (`Low`, `Medium`, `High`, `Critical`).
2. **IP & Timestamp Sanitization:**
   * Validates IP addresses using IPv4/IPv6 regular expressions.
   * Normalizes timestamps into standardized ISO-8601 UTC strings (`YYYY-MM-DDTHH:MM:SSZ`).
3. **Event Normalization Lookup:**
   Maps hundreds of arbitrary aliases into uniform PascalCase identifiers via `EVENT_NORMALIZATION_MAP`:
   * `"port scan"`, `"port_scan"` ➔ `"PortScan"`
   * `"sqli"`, `"sql injection"` ➔ `"SQLInjection"`
   * `"priv_esc"`, `"privilege escalation"` ➔ `"PrivilegeEscalation"`
   * `"c2_beacon"`, `"beaconing"` ➔ `"C2Beacon"`
4. **Multi-Tenant Security:**
   Automatically stamps each validated alert with the authenticated tenant's `user_id`, enforcing strict tenant-level row isolation.

### 3. Concrete Example
* **Raw CSV Line:**
  ```csv
  2026-09-19 03:10:00, 192.168.1.100, 10.0.0.5, port scan, med
  ```
* **Normalized Alert Record:**
  ```json
  {
    "timestamp": "2026-09-19T03:10:00Z",
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.5",
    "event": "PortScan",
    "severity": "Medium",
    "user_id": "tenant-uuid-1234"
  }
  ```

---

## 🔹 Step 2: Alert Correlation Engine

* **Source File:** [`src/backend/services/alert_correlation.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/services/alert_correlation.py)
* **Component:** `AlertCorrelationEngine`

### 1. The Challenge
A Security Operations Center (SOC) receives 10,000–50,000 alerts per day. Looking at individual alerts in isolation hides the broader context: an attacker rarely stops at one action. They scan, breach, escalate privileges, and steal data over minutes or hours.

### 2. How It Operates
1. **Source-IP Grouping:** Alerts are partitioned by their origin (`src_ip`), linking all actions initiated by the same adversary.
2. **Sliding Time Window (30 Minutes):**
   * Configured via `DEFAULT_TIME_WINDOW_MINUTES = 30`.
   * If subsequent alerts from the same IP occur within 30 minutes of a previous event, the window slides forward and merges the alert into the active chain.
   * If an adversary pauses for longer than 30 minutes, a separate distinct campaign chain is instantiated.
3. **Kill-Chain Logical Ordering:**
   Alerts within an attack chain are ordered chronologically and weighted by `ATTACK_STAGE_ORDER` (from initial Reconnaissance down to Data Exfiltration):
   * Stage 0: `Reconnaissance` / `PortScan`
   * Stage 3: `BruteForce` / `CredentialAccess`
   * Stage 7: `PrivilegeEscalation`
   * Stage 14: `DataExfiltration`
4. **Deterministic Guarantee:**
   **Zero LLM involvement.** Correlation uses deterministic grouping algorithms to guarantee that identical input logs always generate identical attack chains without false links or hallucinated steps.

### 3. Concrete Example
* **Incoming Fragmented Alerts:**
  * 03:00 AM — `198.51.100.23` ➔ `PortScan` on `10.0.0.5`
  * 03:12 AM — `198.51.100.23` ➔ `BruteForce` on `10.0.0.5`
  * 03:22 AM — `198.51.100.23` ➔ `DataExfiltration` on `10.0.0.5`
* **Correlated Output:**
  * **Attack Chain ID:** `AC001`
  * **Adversary IP:** `198.51.100.23`
  * **Event Count:** 3 events unified into a single chronological narrative spanning 22 minutes.

---

## 🔹 Step 3: Automated MITRE ATT&CK® Mapping

* **Source File:** [`src/backend/services/mitre_mapping.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/services/mitre_mapping.py)
* **Component:** `MitreMappingService`

### 1. The Challenge
Raw technical event names (e.g., `"BruteForce"`) do not explain attacker intent or align with global cybersecurity frameworks. Security teams rely on the **MITRE ATT&CK®** framework to communicate tactics, techniques, and procedures (TTPs) across teams and leadership.

### 2. How It Operates
1. **Configurable Knowledge Base:**
   Utilizes an extensible, deterministic lookup table (`MITRE_KNOWLEDGE_BASE`) matching normalized security events to standardized ATT&CK IDs.
2. **Tactical & Technique Categorization:**
   Assigns explicit metadata for each event in the attack chain:
   * **`PortScan`** ➔ **`T1595`** (*Active Scanning*) | Tactic: `Reconnaissance`
   * **`BruteForce`** ➔ **`T1110`** (*Brute Force*) | Tactic: `Credential Access`
   * **`PrivilegeEscalation`** ➔ **`T1068`** (*Exploitation for Privilege Escalation*) | Tactic: `Privilege Escalation`
   * **`DataExfiltration`** ➔ **`T1048`** (*Exfiltration Over Alternative Protocol*) | Tactic: `Exfiltration`
3. **Heatmap & Matrix Visualization:**
   Maps technique progression into matrix columns on the frontend dashboard, allowing analysts to visualize adversary movement across stages.

### 3. Concrete Example
```json
{
  "event": "BruteForce",
  "technique_id": "T1110",
  "technique_name": "Brute Force",
  "tactic": "Credential Access",
  "description": "Adversaries may use brute force techniques to attempt credential access."
}
```

---

## 🔹 Step 4: Deterministic Mathematical Risk Scoring

* **Source File:** [`src/backend/services/risk_scoring.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/services/risk_scoring.py)
* **Component:** `RiskScoringEngine`

### 1. The Challenge
Using generic LLM prompts to assign risk scores produces non-deterministic hallucinations: asking an AI twice for a severity score on the exact same log might return `72` then `89`. In regulated environments and SOC audits, scores must be mathematically reproducible and auditable.

### 2. How It Operates
TimonTrack executes an auditable mathematical calculation:

$$\text{Risk Score} = \min\Big(100, \text{Base Event Score} + \text{MITRE Tactic Score} + \text{Chain Complexity Bonus}\Big)$$

1. **Event Base Weights (`EVENT_WEIGHTS`):**
   Reflects the intrinsic threat severity of the activity:
   * `DataExfiltration`: **70 pts**
   * `Ransomware`: **60 pts**
   * `Malware`: **50 pts**
   * `PrivilegeEscalation`: **45 pts**
   * `CredentialDumping`: **40 pts**
   * `BruteForce`: **25 pts**
   * `PortScan`: **10 pts**
2. **MITRE Tactic Weights (`MITRE_TACTIC_WEIGHTS`):**
   Escalates points as adversaries progress deeper into the kill chain:
   * `Exfiltration`: **+30 pts**
   * `Impact`: **+25 pts**
   * `Credential Access`: **+20 pts**
   * `Privilege Escalation`: **+20 pts**
   * `Initial Access`: **+10 pts**
   * `Reconnaissance`: **+5 pts**
3. **Chain Complexity Bonus:**
   Adds compounding weight based on the number of distinct attacked hosts, unique technique categories, and total event volume.
4. **Severity Tier Classification:**
   * 🔴 **Critical:** 80 – 100
   * 🟠 **High:** 60 – 79
   * 🟡 **Medium:** 35 – 59
   * 🟢 **Low:** 0 – 34

### 3. Concrete Example
* **Incident A (Isolated Probe):**
  * `PortScan` (10 pts) + `Reconnaissance` tactic (5 pts) = **Score: 15 (Low)**
* **Incident B (Full Intrusion Campaign):**
  * `PortScan` + `BruteForce` + `DataExfiltration` + multi-stage bonus = **Score: 94 (Critical)**
  * Generates an auditable breakdown explaining exactly why the incident reached Critical severity.

---

## 🔹 Step 5: AI Intelligence Synthesis & Playbooks

* **Source Files:**
  * [`src/backend/agents/bluf_report_agent.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/agents/bluf_report_agent.py)
  * [`src/backend/agents/recommendation_agent.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/agents/recommendation_agent.py)
  * [`src/backend/services/qdrant_service.py`](file:///d:/Projects/IBM/bob-ai-hackathon-Timon/src/backend/services/qdrant_service.py)
* **Models:** Llama 3.3 70B (via Groq Cloud) / IBM watsonx.ai + FastEmbed (`bge-small-en-v1.5`)

### 1. The Challenge
After detecting and scoring an intrusion, analysts must write executive incident summaries for senior leadership and look up manual firewall/containment commands. This triage and documentation takes **3 to 6 hours per incident**.

### 2. How It Operates
TimonTrack utilizes specialized LangGraph LLM agents with strictly enforced Pydantic schemas:

1. **BLUF Report Agent (Executive Briefing):**
   * Synthesizes the attack chain, MITRE IDs, affected IPs, and risk scores into a **Bottom Line Up Front** briefing.
   * Delivers:
     * High-level incident synopsis.
     * Crown-jewel assets at risk.
     * Potential business and compliance impact.
     * Attacker intent and sophistication analysis.
2. **Tactical Recommendation Agent (Incident Playbook):**
   * Formulates a structured 4-tier tactical action plan:
     * **Immediate Containment:** Isolation of affected subnets, firewall rules to drop attacker IP, token revocation.
     * **Investigation Guidance:** Forensic log locations, specific bash/PowerShell history commands, memory dump targets.
     * **Long-Term Hardening:** Patching recommendations, MFA enforcement, network micro-segmentation.
     * **Validation Checks:** Verification queries to ensure adversary persistence is eliminated.
3. **Vector Synchronization & Semantic Search:**
   * Generates dense 384-dimensional vector embeddings using FastEmbed.
   * Upserts the incident narrative into the **Qdrant Vector Database**.
   * Empowers the **Interactive SOC Copilot Chat** to answer natural language questions (e.g., *"Which internal hosts communicated with Russian IPs yesterday?"*) with sub-millisecond grounded retrieval (RAG).

### 3. Concrete Example
* **BLUF Executive Output:**
  > *"At 03:00 UTC, host 10.0.0.5 was targeted by external IP 198.51.100.23 in a multi-stage intrusion that progressed from network discovery to credential brute-forcing, culminating in unauthenticated data exfiltration. Estimated risk is Critical (94/100). Containment initiated."*
* **Tactical Containment Command Generated:**
  ```bash
  iptables -A INPUT -s 198.51.100.23 -j DROP
  aws ec2 stop-instances --instance-ids i-0abc123def456
  ```

---

## 📊 Summary Comparison

| Step | Engine / Module | Input | Output | AI / Deterministic |
| :--- | :--- | :--- | :--- | :--- |
| **1. Ingestion** | `csv_parser.py` | Messy CSV / Logs | Normalized `Alert` Objects | Deterministic |
| **2. Correlation** | `alert_correlation.py` | Individual Alerts | Unified `AttackChain` (`AC001`) | Deterministic (30-min window) |
| **3. MITRE Mapping** | `mitre_mapping.py` | Event Strings | ATT&CK IDs (`T1595`, `T1110`, etc.) | Deterministic (Knowledge Base) |
| **4. Risk Scoring** | `risk_scoring.py` | Chain + MITRE Data | 0–100 Mathematical Score | Deterministic (Weighted Formula) |
| **5. AI Synthesis** | `bluf_report_agent.py` & `recommendation_agent.py` | Enriched Attack Chain | Executive BLUF + Containment Playbook + Qdrant Embeddings | AI / LLM (Llama 3.3 70B via Groq / watsonx) |
