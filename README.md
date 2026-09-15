# 🚀 Timon THRETINTAL

Threat Intelligence Correlation & Alert Prioritisation Assistant

## 👥 Team

| Field | Value |
|---|---|
| Team Name | TimonTrack |
| Track | AI |
| Team Lead | Abhi Kakadiya — abhikakadiya1043@gmail.com |
| Members | Jaimin, Digisha, Om |

## 🎯 Problem Statement

Security Operations Center teams receive large volumes of fragmented alerts from SIEMs, endpoint tools, network sensors, and intelligence feeds. Analysts spend too much time investigating false positives and manually connecting related events, which delays the identification and response to real multi-stage threats.

## 💡 Solution

Sentinel Forge is an AI-assisted threat intelligence platform that ingests security alerts, normalizes and correlates them into attack chains, maps activity to MITRE ATT&CK, and prioritizes risk. It also generates BLUF intelligence reports, tactical recommendations, and provides an authenticated analyst copilot grounded in the project’s telemetry.

## ✨ Key Features

- Multi-source CSV/JSON alert ingestion and validation
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
src/                  # All source code
  backend/            # FastAPI API, AI workflows, services, and tests
  frontend/           # React/Vite SOC application
docs/                 # Written documentation
  problem-statement.md
  solution-overview.md
  architecture.md
  setup-guide.md
demo/                 # Demo artifacts
  screenshots/        # App screenshots
  demo-video-link.txt # Link to demo video
presentation/         # Slide deck and presentation assets
submission.yaml       # Structured submission metadata
main.py               # Root FastAPI entry point
requirements.txt      # Backend dependencies
README.md             # Project documentation
```

## ⚡ How to Run

### 1. Clone the repo

```bash
git clone https://github.com/Abhi-1100/bob-ai-hackathon-Timon.git
cd bob-ai-hackathon-Timon
```

### 2. Install dependencies

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

cd src/frontend
npm install
cd ../..
```

### 3. Configure environment

```bash
# Linux/macOS
cp src/.env.example .env
# Windows PowerShell
Copy-Item src/.env.example .env
```

Edit `.env` with your values. At minimum, configure:

```dotenv
DATABASE_URL=sqlite:///./sentinel_forge.db
GROQ_API_KEY=your_groq_api_key
JWT_SECRET=replace_with_a_long_random_secret
```

For the frontend, create `src/frontend/.env` if the backend is not running at the default URL:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Run the project

Start the backend from the repository root:

```bash
python main.py
```

In a second terminal, start the frontend:

```bash
cd src/frontend
npm run dev
```

Open `http://localhost:5173`. The backend API and Swagger documentation are available at `http://localhost:8000` and `http://localhost:8000/docs`.

### Tests and production build

```bash
python -m pytest src/backend/tests -v
npm --prefix src/frontend run build
```

## 🖥 Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | See [demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | See [demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼 Screenshots | See [demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | See [presentation/](presentation/) |

## ⚠️ Known Limitations

- Local development uses in-memory Qdrant when no remote Qdrant URL is configured.
- AI-generated reports, recommendations, and analyst chat require a configured model provider such as Groq or watsonx.ai.
- The default development setup uses SQLite; production deployments should use a managed PostgreSQL-compatible database.
- The frontend production bundle is currently large and may benefit from additional code splitting.

## 🏅 What We're Most Proud Of

Sentinel Forge turns noisy, disconnected security alerts into explainable attack chains with MITRE ATT&CK context, transparent risk prioritization, and actionable BLUF summaries. The strongest part of the submission is the end-to-end workflow connecting ingestion, correlation, scoring, reporting, and analyst chat in one SOC experience.
