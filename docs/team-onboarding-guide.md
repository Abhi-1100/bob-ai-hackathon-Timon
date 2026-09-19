# 🛡️ TimonTrack — ThreatIntel: Team Onboarding & Project Primer

> **One-Liner:** An AI-powered threat correlation and prioritization platform that turns thousands of noisy, fragmented security alerts into unified attack chains, maps attacker techniques to MITRE ATT&CK®, calculates deterministic risk scores, and generates executive BLUF briefings and tactical remediation playbooks in seconds.

---

## 💡 1. Cybersecurity 101: The Problem in Simple Terms

If you are new to cybersecurity, here is the real-world challenge in everyday terms:

* **What is a SOC (Security Operations Center)?**  
  The 24/7 security control room of an enterprise. Analysts watch dashboards around the clock to detect intruders, malware, and data breaches.
* **The "50,000 Smoke Alarms" Problem (Alert Fatigue):**  
  Large companies deploy dozens of security tools (firewalls, antiviruses, cloud scanners). Every day, these tools produce **10,000 to 50,000 individual alerts**.  
  Over **70% of them are false alarms** or harmless background noise (e.g., someone typing the wrong password, or an IT administrator running a routine scan).
* **The Danger:**  
  Because human analysts are overwhelmed by noise, they suffer from **alert fatigue**. Meanwhile, a real hacker executing a multi-stage intrusion sneaks through undetected because their steps are scattered across thousands of disconnected logs.

---

## 🎯 2. Why Real Attacks Get Missed: Fragmented Telemetry

Real attackers don't perform just one isolated action. They run multi-step campaigns:
1. **Reconnaissance:** Scanning network ports for open doors.
2. **Initial Access / Brute Force:** Guessing passwords or using stolen credentials to get in.
3. **Privilege Escalation:** Elevating rights to Administrator or Root.
4. **Data Exfiltration:** Stealing sensitive customer or financial data.

**The Current Pain:**  
Traditional SIEM tools see these 4 actions as 4 separate, unrelated logs from different sensors. Analysts have to manually query multiple systems, piece together timestamps, and spend **3 to 6 hours** just writing an incident report for leadership.

---

## 🚀 3. What Our Project Does (The Solution)

**TimonTrack** acts like an **automated, AI-powered security detective**:

1. **Ingestion & Normalization:** Ingests raw, messy alert streams (CSV / JSON) and standardizes them.
2. **Alert Correlation Engine:** Automatically connects the dots! It links events sharing the same source IP and happening within a 30-minute window into a single chronological **Attack Chain** (e.g., `AC001`).
3. **MITRE ATT&CK® Mapping:** Translates technical logs into the global adversary playbook (e.g., identifies *T1046 Network Scanning* or *T1110 Brute Force*).
4. **Deterministic Risk Scoring:** Calculates an exact, mathematical risk score (0–100) based on severity, MITRE tactics progression, and chain complexity (eliminating AI guessing/hallucinations for scores).
5. **AI BLUF Briefings & Playbooks:** Uses LLMs (Llama 3.3 70B / watsonx) to produce **BLUF (Bottom Line Up Front)** executive summaries and prioritized tactical containment steps.
6. **Interactive SOC Copilot:** Analysts can ask questions in plain English (*"What credential access attempts happened today?"*) and receive grounded, accurate answers backed by vector search.

---

## 🔄 4. End-to-End System Pipeline

```
[Raw Security Alerts / CSV Feed]
                │
                ▼
  [1. Ingestion & Normalization]
    • Validates schema (timestamp, src_ip, dst_ip, event, severity)
    • Enforces multi-tenant user isolation
                │
                ▼
  [2. Alert Correlation Engine]
    • Groups alerts across 30-min sliding windows and common IPs
    • Reconstructs chronological Attack Chains (e.g., AC001)
                │
                ▼
  [3. Automated MITRE ATT&CK Mapping]
    • Tags tactics (Initial Access, Execution, Credential Access, etc.)
    • Maps specific technique IDs (T1046, T1110, T1078)
                │
                ▼
  [4. Deterministic Risk Scoring Engine]
    • Score = min(100, EventScore + MitreScore + ChainBonus)
    • Categorizes into Critical (80+), High (60-79), Medium (35-59), Low (<35)
                │
                ▼
  [5. LangGraph AI Orchestration]
    • BLUF Report Agent: Synthesizes executive briefings
    • Recommendation Agent: Generates 4-tier tactical containment actions
                │
                ▼
  [6. Qdrant Vector Synchronization]
    • Embeds attack chain narratives via FastEmbed (384d vectors)
    • Enables sub-millisecond semantic search
                │
                ▼
  [7. Analyst Copilot & Glassmorphic SOC UI]
    • Grounded RAG chat with conversation memory
    • Live KPI charts, MITRE matrix, attack chain inspector
```

---

## 👥 5. Target Users & Value Delivered

| Role | Pain Point | How TimonTrack Solves It |
|---|---|---|
| **Tier-1/2 SOC Analyst** | Overwhelmed by 10,000+ alerts daily; repetitive manual triage. | Groups alerts into attack chains, slashes noise by >70%, and provides an AI copilot to investigate incidents in plain English. |
| **Incident Response Lead** | Spends hours manually stitching logs to build timelines. | Automatically reconstructs chronological attacker steps mapped to MITRE ATT&CK. |
| **CISO / Commander** | Needs immediate high-level risk overview, not raw log dumps. | Receives 1-page **BLUF (Bottom Line Up Front)** briefings and live risk distributions in seconds. |

---

## 🛠️ 6. Tech Stack at a Glance

* **Frontend:** React 18, Vite, Lucide Icons, Recharts, Custom Glassmorphic Dark UI
* **Backend API:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2
* **Databases:** PostgreSQL (Neon Cloud) / SQLite, SQLAlchemy ORM
* **Caching:** Upstash Redis (L2) + In-memory (L1) with tenant-scoped keys
* **Vector Database:** Qdrant Vector Store + FastEmbed (`BAAI/bge-small-en-v1.5`)
* **AI & LLM Orchestration:** LangGraph, LangChain, Groq Cloud (`llama-3.3-70b-versatile`) / IBM watsonx.ai
* **Testing:** Pytest (106 unit & integration tests)

---

## 📂 7. Key Code Locations

```
src/
├── backend/
│   ├── main.py                     # FastAPI entry point & routes registration
│   ├── services/
│   │   ├── csv_parser.py           # Ingestion & normalization of alert data
│   │   ├── alert_correlation.py    # Temporal grouping into Attack Chains
│   │   ├── mitre_mapping.py        # Mapping alerts to MITRE tactics & techniques
│   │   ├── risk_scoring.py         # Deterministic 0–100 mathematical risk scoring
│   │   └── qdrant_service.py       # FastEmbed vector embeddings & Qdrant sync
│   ├── agents/
│   │   ├── bluf_report_agent.py    # Executive BLUF report generation
│   │   └── recommendation_agent.py # Tactical remediation & containment playbooks
│   └── chat/
│       └── analyst_chat.py         # Grounded RAG conversational copilot
└── frontend/
    ├── main.jsx                    # React app entry point & routing
    ├── pages/                      # 12 SOC dashboard views
    ├── components/                 # Visualizers (Attack graph, MITRE matrix)
    └── styles.css                  # Glassmorphism dark-mode styles
```

---

## ⚡ 8. How to Run Locally

### 1. Backend (FastAPI)
```bash
cd src/backend
# Create and configure your environment
cp ../.env.example .env
# Edit .env with your GROQ_API_KEY

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive API Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend (React + Vite)
```bash
cd src/frontend
npm install
npm run dev
```
* SOC Dashboard: `http://localhost:5173`

### 3. Run Automated Tests
```bash
pytest src/backend/tests/ -v
```

---

## 📋 9. Quick Copy-Paste Message for Slack / WhatsApp / Discord

*(Copy and send this directly to your team channel!)*

> 👋 **Hey team!** Here is a quick breakdown of our project (**TimonTrack / ThreatIntel**):
> 
> 🎯 **The Problem:** 
> Companies get 10,000–50,000 security alerts a day. Most are false alarms, causing massive "alert fatigue", while multi-stage cyber attacks get lost in the noise.
> 
> 💡 **What Our System Does:**
> 1. **Ingests & Cleans** raw alert feeds.
> 2. **Correlates** scattered alerts into continuous **Attack Chains** (combining events by IP and 30-min time windows).
> 3. **Maps** attacks to the standard **MITRE ATT&CK®** framework.
> 4. **Calculates a 0–100 Risk Score** using transparent math (no AI hallucination for scoring).
> 5. **Generates Executive BLUF Reports** and tactical containment steps using **LangGraph + Llama 3.3 / watsonx**.
> 6. **Powers an AI SOC Copilot** with Qdrant vector search so analysts can chat and investigate in plain English.
> 
> 🛠️ **Tech Stack:** FastAPI (Python), React 18 + Vite (Dark Glassmorphic UI), PostgreSQL, Qdrant Vector DB, Upstash Redis, LangGraph, Groq Llama 3.3.
> 
> 📖 Check out the full guide in `docs/team-onboarding-guide.md` in our repository!
