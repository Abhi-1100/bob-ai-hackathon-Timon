# 🚀 TimonTrack — ThreatIntel
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
| **Team Lead** | Abhi Kakadiya — 24it035@charusat.edu.in |
| **Members** | Jaimin Parmar (24ce073@charusat.edu.in), Digisha Savaliya (24it087@charusat.edu.in), Om Ghori (24dce43@charusat.edu.in) |

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

**ThreatIntel** is an end-to-end, AI-driven threat intelligence and alert prioritization platform built with **FastAPI**, **LangGraph**, **Qdrant Vector Database**, and **React 18 + Vite**.

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

```
bob-ai-hackathon-Timon/
│
├── submission.yaml          # Structured metadata — read by evaluators & validation CI
├── README.md                # Project overview — human-readable entry point
├── CONTRIBUTING.md          # Submission instructions & guidelines
├── .gitignore               # Pre-configured gitignore
│
├── src/                     # All application source code
│   ├── backend/             # FastAPI Application & LangGraph AI Pipeline
│   │   ├── agents/          # AI Agents (BLUF report & tactical recommendations)
│   │   ├── chat/            # Grounded RAG Analyst Chat service
│   │   ├── database/        # Database models and session management
│   │   ├── graph/           # LangGraph workflow definitions
│   │   ├── nodes/           # Workflow processing nodes
│   │   ├── repositories/    # Data access repositories
│   │   ├── routers/         # FastAPI API routers
│   │   ├── sample_data/     # Enterprise threat alerts datasets (1,000 alerts)
│   │   ├── schemas/         # Pydantic data schemas
│   │   ├── services/        # Core business logic (correlation, MITRE, risk, Qdrant)
│   │   ├── tests/           # Comprehensive test suite (106 unit & integration tests)
│   │   ├── main.py          # FastAPI application entry point
│   │   └── requirements.txt # Python dependencies
│   ├── frontend/            # React 18 + Vite SOC Dashboard
│   │   ├── components/      # UI components & Attack Graph visualizers
│   │   ├── pages/           # 12 SOC dashboard views
│   │   ├── services/        # Backend API integration client
│   │   ├── store/           # Zustand state management
│   │   ├── package.json     # Node package manifest
│   │   └── styles.css       # SOC glassmorphism UI styles
│   ├── scripts/             # Telemetry generator and maintenance scripts
│   ├── .env.example         # Template for environment variables
│   └── README.md            # Brief note on src/ layout
│
├── docs/                    # Written documentation
│   ├── problem-statement.md # Detailed problem context and pain points
│   ├── solution-overview.md # Technical solution mechanism & design decisions
│   ├── architecture.md      # Architecture diagrams & component interactions
│   └── setup-guide.md       # Step-by-step local setup & deployment guide
│
├── demo/                    # Demo artifacts
│   ├── demo-video-link.txt  # Link to 3-5 minute demonstration video
│   ├── live-demo-url.txt    # Public URL to deployed live application
│   └── screenshots/         # 10 platform screenshots + visual gallery
│
├── presentation/            # Slide deck
│   ├── slides.pptx          # Hackathon presentation slide deck
│   └── README.md            # Presentation guidelines
│
└── .github/
    └── workflows/
        └── validate.yml     # Automated submission validator
```

---

## ⚡ How to Run

### 1. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd src/backend

# Configure environment variables
cp ../.env.example .env
# Edit .env with your GROQ_API_KEY / WATSONX credentials

# Install backend dependencies
pip install -r requirements.txt

# Run backend with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

### 2. Frontend Setup (React + Vite)

```bash
# Navigate to frontend directory
cd src/frontend

# Install dependencies
npm install

# Run Vite development server
npm run dev
```

- **SOC Web Dashboard:** `http://localhost:5173`

### 3. Running Automated Tests

```bash
# Run backend test suite (106 unit & integration tests)
pytest src/backend/tests/ -v

# Test frontend production build
npm --prefix src/frontend run build
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [bob-ai-hackathon-timon-puce.vercel.app](https://bob-ai-hackathon-timon-puce.vercel.app/) |
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
