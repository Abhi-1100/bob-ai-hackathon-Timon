# 🚀 TimonTrack — Sentinel Forge
### Threat Intelligence Correlation & Alert Prioritisation Assistant

> **Track:** AI  
> **Challenge:** Threat Intelligence Correlation & Alert Prioritisation Assistant  
> **Mission:** Ingest multi-source threat feeds, correlate cross-domain alerts to eliminate false positives, map attacker techniques to the MITRE ATT&CK® framework, dynamically rank threats, and autonomously synthesize high-priority BLUF (Bottom Line Up Front) intelligence summaries with an interactive SOC analyst copilot.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | TimonTrack |
| **Track** | AI |
| **Team Lead** | Abhi Kakadiya — abhikakadiya1043@gmail.com |
| **Members** | Jaimin, Digisha, Om |

---

## 🎯 Problem Statement

> See [`docs/problem-statement.md`](docs/problem-statement.md) and [`PRD_Threat_Intelligence_Assistant.md`](PRD_Threat_Intelligence_Assistant.md) for full specifications.

Security Operations Centers (SOCs) and defence analysts face severe **alert fatigue**, receiving tens of thousands of fragmented alerts daily from disparate sources:
- **Enterprise SIEMs** (Splunk, QRadar, Elastic)
- **Tactical Cyber Sensors** (network intrusion detection, endpoint telemetry, firewalls)
- **Satellite & Telemetry feeds** (orbital telemetry, downlink anomalies)
- **OSINT & Intelligence Feeds** (unstructured threat bulletins, CVE advisories)

**Core Pain Points:**
1. **False Positive Overload:** Chasing noise wastes vital defense resources while coordinated multi-stage intrusions remain buried.
2. **Schema Fragmentation:** Incompatible alert schemas prevent cross-feed correlation in real time.
3. **Delayed Decision Cycles:** Commanders and SOC leads require concise, high-confidence **BLUF (Bottom Line Up Front)** intelligence in minutes, not hours.

---

## 💡 Solution

**Sentinel Forge** is an end-to-end, AI-driven threat intelligence and alert prioritization platform built with **FastAPI**, **LangGraph**, **Qdrant Vector Database**, and **React 18 + Vite**.

1. **Multi-Source Ingestion & Normalization:** Ingests heterogeneous alert streams into a canonical schema.
2. **Correlation & Campaign Reconstruction:** Groups related alerts into Attack Chains across time windows and host relationships.
3. **Automated MITRE ATT&CK® Mapping:** Correlates observed attacker behavior to MITRE enterprise tactics and techniques.
4. **Dynamic Risk Scoring:** Evaluates multi-factor risk scores (0–100) and classifies threats into Critical, High, Medium, and Low.
5. **AI Executive BLUF Briefings & Recommendations:** Uses LLM agents (Llama 3.3 70B / watsonx foundation models) to deliver actionable commander briefs and tactical containment steps.
6. **SOC Analyst Interactive Chat:** Grounded RAG-based analyst chatbot providing real-time question answering over attack chains and telemetry.

---

## ✨ Key Features

- **Multi-Source Alert Ingestion Engine:** Automated ingestion and validation for CSV/JSON security feeds.
- **Rule-Based & Semantic Correlation:** Clusters alerts into attack chains to slash noise and false positives.
- **Automated MITRE ATT&CK® Framework Alignment:** Automatically tags attack techniques and tactics.
- **Deterministic 4-Tier Risk Scoring Engine:** Prioritizes critical attack chains with transparent mathematical scoring.
- **AI Executive BLUF Generator & Tactical Playbooks:** Formulates executive summaries and prioritized remediation playbooks.
- **Interactive SOC Analyst Copilot:** LangGraph + Qdrant grounded retrieval-augmented chat assistant.
- **Real-Time Glassmorphic SOC Dashboard:** Dark-mode React/Vite interface with live metrics, attack chain visualizer, and MITRE matrix.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.11+, JavaScript / JSX, SQL |
| **Backend Frameworks** | FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, Alembic |
| **AI / Orchestration** | LangGraph, LangChain, Groq (Llama 3.3 70B), Qdrant Vector Store, FastEmbed |
| **Frontend Frameworks** | React 18, Vite, Lucide Icons, Vanilla CSS Design System |
| **Databases** | SQLite (embedded), PostgreSQL / Neon compatible |
| **DevOps & Testing** | Pytest, GitHub Actions, Docker |

---

## 📁 Repository Structure

All project source code is organized inside `src/` following monorepo guidelines:

```
├── src/
│   ├── backend/              # FastAPI Application & AI Pipeline
│   │   ├── agents/           # AI Agents (BLUF report & tactical recommendations)
│   │   ├── chat/             # Analyst Chat service
│   │   ├── database/         # Database models and session management
│   │   ├── graph/            # LangGraph workflow definitions
│   │   ├── migrations/       # Alembic migrations
│   │   ├── nodes/            # Workflow processing nodes
│   │   ├── repositories/     # Data access repositories
│   │   ├── routers/          # FastAPI API routers
│   │   ├── sample_data/      # Sample dataset & generator
│   │   ├── schemas/          # Pydantic data schemas
│   │   ├── services/         # Core business logic (correlation, MITRE, risk scoring, Qdrant)
│   │   ├── tests/            # Test suite (106 unit & integration tests)
│   │   ├── uploads/          # Alert CSV upload staging
│   │   ├── main.py           # FastAPI entry point
│   │   └── requirements.txt  # Backend dependencies
│   │
│   └── frontend/             # React 18 + Vite SOC Dashboard
│       ├── services/         # API integration client
│       ├── index.html        # Vite entry HTML
│       ├── main.jsx          # SOC dashboard root application
│       ├── package.json      # Node package manifest
│       └── styles.css        # SOC glassmorphism UI styles
│
├── demo/                     # Demo recordings & screenshots
├── docs/                     # Full system architecture & setup guides
├── presentation/             # Hackathon presentation slides
├── sample_data/              # Enterprise threat alerts dataset (1,000 alerts)
├── main.py                   # Root runner for backend
├── package.json              # Root package runner for frontend
├── index.html                # Root HTML template for Vite
├── submission.yaml           # Hackathon submission metadata
└── README.md                 # Project documentation
```

---

## ⚡ How to Run

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Abhi-1100/bob-ai-hackathon-Timon.git
cd bob-ai-hackathon-Timon

# Install backend dependencies
pip install -r src/backend/requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your GROQ_API_KEY / WATSONX credentials

# Run backend from root
python main.py
# Or run with uvicorn
uvicorn main:app --reload
```

- Backend API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# From workspace root
npm install
npm run dev

# Or directly in src/frontend
cd src/frontend
npm install
npm run dev
```

- Frontend SOC Dashboard: `http://localhost:5173`

### 3. Running Automated Tests

```bash
# Run backend test suite
python -m pytest src/backend/tests -v
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- Vector search uses local in-memory Qdrant by default unless remote `QDRANT_URL` is supplied.
- Threat alert CSVs larger than 50MB should be uploaded in chunks.
- watsonx.ai integration can fall back to local/Groq Llama 3.3 models in offline development environments.

---

## 🏅 What We're Most Proud Of

- Fully autonomous, explainable threat correlation pipeline linking raw SIEM alerts to MITRE ATT&CK techniques in seconds.
- Multi-agent LangGraph workflow producing commander-ready BLUF executive summaries and concrete tactical remediation steps.
- Interactive, grounded RAG analyst copilot with persistent session memory.
- Modern, glassmorphic SOC dashboard delivering a responsive dark-mode analyst experience.

---

## 🔗 Repository

[https://github.com/Abhi-1100/bob-ai-hackathon-Timon](https://github.com/Abhi-1100/bob-ai-hackathon-Timon)
