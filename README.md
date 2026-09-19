# 🚀 TimonTrack — ThreatIntel
### Threat Intelligence Correlation & Alert Prioritisation Assistant

Threat Intelligence Correlation & Alert Prioritisation Assistant

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | TimonTrack |
| **Track** | AI |
| **Team Lead** | Abhi Kakadiya — 24it035@charusat.edu.in / abhikakadiya1043@gmail.com |
| **Members** | Jaimin Parmar (24ce073@charusat.edu.in), Digisha Savaliya (24it087@charusat.edu.in), Om Ghori (24dce43@charusat.edu.in) |

---

## 🎯 Problem Statement

Security Operations Center (SOC) teams receive large volumes of fragmented alerts from SIEMs, endpoint tools, network sensors, and intelligence feeds. Analysts spend too much time investigating false positives and manually connecting related events, which delays the identification and response to real multi-stage threats.

## 💡 Solution

**ThreatIntel** is an end-to-end, AI-driven threat intelligence and alert prioritization platform built with **FastAPI**, **LangGraph**, **Qdrant Vector Database**, and **React 18 + Vite**.

1. **Multi-Source Ingestion & Normalization:** Ingests heterogeneous alert streams (CSV, JSON, streaming API) into a canonical schema.
2. **Correlation & Campaign Reconstruction:** Groups related alerts into Attack Chains across time windows and host relationships.
3. **Automated MITRE ATT&CK® Mapping:** Correlates observed attacker behavior to MITRE enterprise tactics and techniques.
4. **Dynamic Risk Scoring:** Evaluates multi-factor risk scores (0–100) and classifies threats into Critical, High, Medium, and Low.
5. **AI Executive BLUF Briefings & Recommendations:** Uses LLM agents (Llama 3.3 70B / watsonx foundation models) to deliver actionable commander briefs and tactical containment steps.
6. **SOC Analyst Interactive Chat:** Grounded RAG-based analyst chatbot providing real-time question answering over attack chains and telemetry.

---

## ✨ Key Features

- Multi-source CSV/JSON/API alert ingestion and validation
- Cross-alert correlation and attack-chain reconstruction
- Automated MITRE ATT&CK tactic and technique mapping
- Transparent 0–100 risk scoring and severity prioritization
- AI-generated BLUF intelligence reports and remediation recommendations
- Authenticated, user-isolated SOC dashboard with analytics and reports
- RAG-powered AI analyst chat backed by Qdrant

## 🛠 Tech Stack

| Category | Technologies |
|---|---|
| Languages | Python, JavaScript, JSX, SQL |
| Frameworks | FastAPI, React, Vite, LangGraph, LangChain |
| IBM Technologies | IBM watsonx.ai integration support |
| Databases | SQLite, PostgreSQL-compatible databases, Qdrant Vector Database |
| Other | Groq/Llama, SQLAlchemy, Alembic, Zustand, Recharts, Pytest, Render, Vercel |

## 📁 Repository Structure

```text
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
# Copy .env from template
# Set GROQ_API_KEY, DATABASE_URL, etc.

# Install dependencies
pip install -r requirements.txt

# Run backend with uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/`

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

### 3. Tests and Production Build

```bash
# Run backend test suite
pytest src/backend/tests/ -v

# Test frontend production build
npm --prefix src/frontend run build
```

## 🖥 Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [bob-ai-hackathon-timon-puce.vercel.app](https://bob-ai-hackathon-timon-puce.vercel.app/) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- Local development uses in-memory Qdrant when no remote Qdrant URL is configured.
- AI-generated reports, recommendations, and analyst chat require a configured model provider such as Groq or watsonx.ai.
- The default development setup uses SQLite; production deployments should use a managed PostgreSQL-compatible database.

## 🏅 What We're Most Proud Of

Sentinel Forge turns noisy, disconnected security alerts into explainable attack chains with MITRE ATT&CK context, transparent risk prioritization, and actionable BLUF summaries. The strongest part of the submission is the end-to-end workflow connecting ingestion, correlation, scoring, reporting, and analyst chat in one unified SOC experience.
