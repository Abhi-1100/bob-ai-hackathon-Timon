# Product Requirements Document (PRD)
## Threat Intelligence Correlation & Alert Prioritisation Assistant

| | |
|---|---|
| **Version** | 1.0.0 |
| **Status** | Draft — Hackathon Build |
| **Derived From** | SRS v1.0.0 (IEEE 830 / ISO/IEC/IEEE 29148) |
| **Event** | IBM BoB AI Innovation Hackathon 2026 |
| **Problem Statement** | Critical Now — Threat Intelligence Correlation & Alert Prioritisation Assistant |
| **Owner** | [Team Name] |
| **Audience** | Full team (Frontend, Backend, AI/ML, DevOps, Presentation) |

---

## 1. Product Overview

### 1.1 Problem
Defence and SOC (Security Operations Center) analysts are flooded with thousands of daily alerts from SIEM systems, satellite feeds, cyber sensors, and intelligence reports — each in a different format. No human team can manually triage this volume. Two failure modes are catastrophic:
- **Missing a genuine threat** amid the noise.
- **Wasting critical resources chasing false positives.**

Commanders also need threat assessments delivered in a **BLUF (Bottom Line Up Front)** format so they can make decisions in minutes, not hours.

### 1.2 Solution Vision
A Bob-powered platform that:
1. Ingests multi-source, multi-format threat alerts.
2. Correlates raw alerts into coherent **attack chains** to separate real threats from noise.
3. Maps attacker behavior to the **MITRE ATT&CK** framework.
4. Scores and prioritizes threats using a deterministic risk model.
5. Generates **AI-assisted, commander-ready BLUF reports**.
6. Provides an **explainable AI Analyst Chat** for follow-up investigation, grounded strictly in retrieved data (zero hallucination).

### 1.3 Why This Matters (Impact)
- Reduces alert fatigue by collapsing 10,000+ raw alerts into a handful of prioritized attack chains.
- Cuts commander decision time from hours of reading raw logs to minutes of reading a structured brief.
- Adds explainability and traceability — every claim in a report or chat answer must be grounded in actual ingested data, which is critical in a defence/security context where false claims are unacceptable.

---

## 2. Goals & Success Metrics

| Goal | Metric | Target (per SRS NFRs) |
|---|---|---|
| Reduce alert noise | Raw alerts → attack chains reduction ratio | Meaningful reduction, no genuine threat dropped |
| Fast triage | Correlation engine processing time | 10,000 alerts correlated in < 3.0 seconds |
| Fast decision support | End-to-end chat answer latency | < 3.0 seconds (hard ceiling 5.0s) |
| Trustworthy AI | Grounding accuracy | 0 fabricated IPs / incidents / MITRE techniques |
| Resilience | System uptime without external APIs | 100% core test pass rate without Groq/network |
| Judge-readiness | Working demo covering full pipeline | CSV upload → BLUF report → Chat, end-to-end |

---

## 3. Target Users / Personas

| Persona | Role | Primary Needs |
|---|---|---|
| **SOC Analyst (Tier 1/2)** | Front-line triage | Fast alert queue, chain drill-down, chat-based investigation |
| **Incident Response Commander / CISO** | Decision-maker | BLUF summaries, risk distribution at a glance, minimal jargon |
| **SIEM / Automated Feed (System actor)** | Machine client | Reliable CSV ingestion endpoint, clear error feedback |
| **Hackathon Judges** | Evaluators | Clear demo flow showing ingestion → correlation → MITRE → risk → BLUF → chat |

---

## 4. Scope

### 4.1 In Scope (MVP for Hackathon)
- CSV-based multi-source alert ingestion (per SRS Module 1–2).
- Attack chain correlation via source-IP clustering + 30-min sliding window (Module 4).
- MITRE ATT&CK technique mapping (Module 5).
- Deterministic 0–100 risk scoring engine (Module 6).
- LLM-generated security recommendations with deterministic fallback (Module 7).
- LLM-generated Executive BLUF report with deterministic fallback (Module 8).
- LangGraph pipeline orchestration end-to-end (Module 9).
- Vector-grounded AI Analyst Chat with session memory (Modules 10–11).
- Frontend UI covering: upload, alert/chain views, MITRE visualization, risk dashboard, BLUF report view, chat interface.

### 4.2 Out of Scope (for hackathon MVP)
- Live/streaming SIEM integration (only CSV batch ingestion required now).
- User authentication/role-based access control (unless required by judges).
- Multi-tenant support.
- Mobile-native app (responsive web is sufficient).
- Editing/overriding AI-generated reports (view-only for MVP unless time allows).

---

## 5. User Stories

### SOC Analyst
- As an analyst, I want to **upload a CSV of raw alerts** so the system can process them without manual sorting.
- As an analyst, I want to **see attack chains instead of raw alert floods** so I can focus on real threats.
- As an analyst, I want to **see MITRE ATT&CK techniques mapped per chain** so I understand attacker intent.
- As an analyst, I want to **ask the AI Analyst Chat follow-up questions** ("What credential access attempts happened today?") and get answers grounded only in real data.
- As an analyst, I want the chat to **tell me clearly when it has no matching data**, instead of guessing.

### Commander / CISO
- As a commander, I want a **one-page BLUF report per attack chain** so I can decide in minutes.
- As a commander, I want to see **risk distribution (Critical/High/Medium/Low counts)** across all active chains at a glance.
- As a commander, I want **recommended actions in plain business language**, not raw technical logs.

### System / DevOps
- As a system operator, I want **graceful fallback when the LLM API is unavailable** so the platform still produces usable (deterministic) output.
- As a system operator, I want **the pipeline to short-circuit safely on failure**, persisting diagnostics instead of crashing.

---

## 6. Functional Requirements (Frontend-Facing Views)

Mapped directly to backend modules/API endpoints defined in the SRS, so the frontend team can build screens with confidence about what data will be available.

### 6.1 Upload & Ingestion Screen
- Drag-and-drop / file-picker CSV upload.
- Calls `POST /api/v1/upload/ingest`.
- Must show validation errors clearly (non-CSV rejected, missing mandatory columns: `timestamp`, `src_ip`, `dst_ip`, `event`, `severity`).
- Show upload success state with record count ingested.

### 6.2 Attack Chain Dashboard
- List/grid of generated attack chains (`GET /api/v1/chains/generate`, `GET /api/v1/chains/{chain_id}`).
- Each chain card shows: Chain ID (`AC001`...), source IP, alert count, time span, severity distribution.
- Sortable/filterable by risk level, MITRE technique, time range.

### 6.3 Attack Chain Detail View
- Chronological event timeline for a chain, following kill-chain stage ordering (Reconnaissance → Initial Access → Post-Exploitation).
- MITRE ATT&CK techniques mapped per event (`POST /api/v1/mitre/map/{chain_id}`), showing technique ID, name, tactic.
- Risk score breakdown (`POST /api/v1/risk/calculate/{chain_id}`): base event score, MITRE score, kill-chain bonus, final 0–100 score, severity label.

### 6.4 Risk Prioritization / Triage View
- Global ranked list of all chains by risk score (`POST /api/v1/risk/calculate-all`).
- Risk distribution widget (`GET /api/v1/risk/distribution`) — counts across Critical/High/Medium/Low.
- Visual priority cues (color-coded severity, e.g. red/orange/yellow/green).

### 6.5 Recommendations Panel
- Per-chain recommendation display (`GET/POST /api/v1/recommendations/{chain_id}`), structured into:
  - Immediate Actions
  - Containment Actions
  - Investigation Actions
  - Prevention Actions
  - Executive Summary (plain-language)
- Visually distinguish AI-generated vs. fallback/deterministic content if the backend flags it.

### 6.6 Executive BLUF Report View
- Clean, print/export-friendly single-page layout (`GET/POST /api/v1/reports/{chain_id}`) with sections:
  - Threat Level
  - Executive Summary
  - Attack Overview (narrative)
  - Affected Assets
  - MITRE Summary
  - Recommended Actions
  - Conclusion
- This is the **commander-facing view** — prioritize clarity, minimal jargon, scannability in under a minute.

### 6.7 Pipeline / Workflow Status View
- Show orchestration progress per chain (`GET /api/v1/workflow/status/{chain_id}`): Load Chain → MITRE → Risk → Recommendations → BLUF → Store.
- Trigger buttons for `run/{chain_id}` and `run-all` for demo purposes.
- Clearly surface failures/short-circuits without crashing the UI.

### 6.8 AI Analyst Chat Interface
- Chat window with session creation (`POST /api/v1/chat/new-session`), message send (`POST /api/v1/chat`), and history retrieval (`GET /api/v1/chat/history/{session_id}`).
- Each AI answer should visually surface: Threat Summary, Risk Assessment, Relevant MITRE Techniques, Recommended Actions (per system prompt rules in SRS 3.11).
- Must clearly render the "no matching threat intelligence records" fallback message when applicable — never let the UI imply an answer is more certain than it is.
- Persistent multi-turn history per session.

---

## 7. Non-Functional Requirements (Frontend-Relevant)

| Category | Requirement |
|---|---|
| **Performance** | Chat responses should visually resolve within ~3s; use loading states, not blocking spinners beyond that. |
| **Trustworthiness/UX** | Any AI-generated content (recommendations, BLUF, chat answers) should be visually distinguishable from raw system data, reinforcing the "zero hallucination, grounded" design constraint. |
| **Resilience** | UI must handle and clearly communicate backend fallback states (e.g., "Generated via deterministic fallback — LLM unavailable") rather than failing silently. |
| **Accessibility/Clarity** | BLUF report view especially must be scannable — commanders need the bottom line in seconds, not minutes. |
| **Cross-platform** | Should work on standard laptop browser resolutions used for judging; responsive is a plus but not the priority for MVP. |

---

## 8. Data Model Reference (for Frontend State Design)

Key entities the frontend will consume (from SRS §3.3 PostgreSQL schema):

- **Upload**: id, file_name, file_path, uploaded_at
- **Alert**: id, upload_id, timestamp, src_ip, dst_ip, event, severity
- **AttackChainDB**: chain_id, source_ip, destination_ips, events, alert_count, start_time, end_time
- **MitreMappingDB**: technique_id, technique_name, tactic, event
- **RiskScoreDB**: score, level, reasoning, event_score, mitre_score, chain_bonus
- **RecommendationDB**: immediate/containment/investigation/prevention actions, executive_summary
- **ReportDB**: threat_level, executive_summary, attack_overview, affected_assets, mitre_summary, recommended_actions, conclusion
- **ChatHistoryDB**: session_id, role, message, created_at

---

## 9. Demo Flow (Recommended, for Judging)

1. Upload a sample multi-source CSV of alerts.
2. Show raw alert count reduced into a handful of attack chains.
3. Drill into one high-risk chain — show MITRE mapping and kill-chain progression.
4. Show the risk score breakdown and global risk distribution dashboard.
5. Show the generated Recommendations panel.
6. Show the Executive BLUF report — emphasize how fast a commander could read this.
7. Open the AI Analyst Chat and ask a follow-up question ("What credential dumping activity occurred?") — show grounded, cited-style answer.
8. Ask a question with no matching data to demonstrate the zero-hallucination fallback message.

---

## 10. Risks & Assumptions

| Risk | Mitigation |
|---|---|
| Groq API key/quota issues during demo | Rely on deterministic fallback synthesizers (already required by SRS §5.3) — test this path explicitly before demo day |
| Frontend/backend integration delays | Agree on API contracts early (this PRD + SRS §4.1 endpoints) and use mock data/fixtures while backend is in progress |
| Time constraints (hackathon deadline) | Prioritize sections 6.1, 6.3, 6.6, 6.8 (Upload, Chain Detail, BLUF Report, Chat) as the "must-demo" MVP if time runs short |
| Judges unfamiliar with cybersecurity jargon | Keep BLUF and Recommendations views in plain language; reserve raw MITRE IDs for a secondary/detail view |

---

## 11. Open Questions for the Team
- Do we need any authentication for the hackathon demo, or is it single-user/local only?
- Should the frontend allow manual re-triggering of individual pipeline stages, or only full `run-all` for simplicity?
- What sample CSV dataset will we use for the live demo, and has it been validated against the required schema (`timestamp`, `src_ip`, `dst_ip`, `event`, `severity`)?
- Do we want an export/print option for the BLUF report (e.g., PDF export) given it's meant for commanders?
