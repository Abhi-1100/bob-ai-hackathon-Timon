# Source Code Layout

This directory contains all application source code for the Threat Intelligence Correlation & Alert Prioritisation Assistant, organised as a clean monorepo.

```
src/
├── backend/                  # FastAPI Application & AI Pipeline
│   ├── agents/               # AI Agents (RecommendationAgent, BLUFReportAgent)
│   ├── chat/                 # Conversational analyst chat service
│   ├── database/             # SQLAlchemy SQLite models and session management
│   ├── graph/                # LangGraph stateful workflow definitions
│   ├── migrations/           # Alembic database migrations
│   ├── nodes/                # Graph processing nodes (retrieve, answer, risk, MITRE)
│   ├── repositories/         # Data access repositories
│   ├── routers/              # FastAPI endpoint routers (upload, correlation, risk, chat, etc.)
│   ├── sample_data/          # Synthetic enterprise threat alert dataset & generator
│   ├── schemas/              # Pydantic schemas and DTOs
│   ├── services/             # Core business logic (MITRE mapping, Qdrant vector RAG, risk scoring)
│   ├── tests/                # Comprehensive unit and integration test suite
│   ├── uploads/              # Temporary alert CSV upload storage
│   ├── main.py               # FastAPI entry point
│   └── requirements.txt      # Python dependencies
│
└── frontend/                 # React 18 + Vite SOC Dashboard
    ├── services/             # API client & backend connection services
    ├── index.html            # Vite HTML entry template
    ├── main.jsx              # React root component & dashboard layout
    ├── package.json          # Node package manifest
    ├── styles.css            # Custom SOC dark-mode glassmorphic design system
    └── .env.example          # Frontend environment variables template
```

## Running the Application

### 1. Backend (FastAPI)

```bash
# From workspace root
pip install -r src/backend/requirements.txt
uvicorn main:app --reload

# Or directly from src/backend
cd src/backend
uvicorn main:app --reload
```

- **Interactive API Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

### 2. Frontend (React + Vite)

```bash
# From workspace root
npm install
npm run dev

# Or from src/frontend
cd src/frontend
npm install
npm run dev
```

- **Dashboard UI:** `http://localhost:5173`
