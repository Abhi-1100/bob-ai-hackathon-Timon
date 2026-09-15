# Source Code Layout

This directory contains all application source code for the Threat Intelligence Correlation & Alert Prioritisation Assistant, organised as a clean monorepo.

```
src/
├── backend/                  # FastAPI Application & AI Pipeline
│   ├── agents/               # AI Agents (RecommendationAgent, BLUFReportAgent)
│   ├── chat/                 # Conversational analyst chat service
│   ├── database/             # SQLAlchemy database models and session management
│   ├── graph/                # LangGraph stateful workflow definitions
│   ├── migrations/           # Alembic database migrations
│   ├── nodes/                # Graph processing nodes (retrieve, answer, risk, MITRE)
│   ├── repositories/         # Data access repositories
│   ├── routers/              # FastAPI endpoint routers (upload, correlation, risk, chat, etc.)
│   ├── sample_data/          # Synthetic & real-world threat alert datasets (1,000 alerts)
│   ├── schemas/              # Pydantic schemas and DTOs
│   ├── services/             # Core business logic (MITRE mapping, Qdrant vector RAG, risk scoring)
│   ├── tests/                # Comprehensive unit and integration test suite
│   ├── uploads/              # Temporary alert CSV upload storage
│   ├── main.py               # FastAPI entry point
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React 18 + Vite SOC Dashboard
│   ├── components/           # UI components, layout, and visualizers
│   ├── pages/                # 12 SOC dashboard views
│   ├── services/             # API client & backend connection services
│   ├── store/                # Zustand stores for auth & analyst chat
│   ├── index.html            # Vite HTML entry template
│   ├── main.jsx              # React root component & dashboard router
│   ├── package.json          # Node package manifest
│   ├── styles.css            # Custom SOC dark-mode glassmorphic design system
│   └── .env.example          # Frontend environment variables template
│
├── scripts/                  # Data generation & maintenance scripts
├── .env.example              # Central environment variables template
└── README.md                 # Source directory overview
```

## Running the Application

### 1. Backend (FastAPI)

```bash
cd src/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

### 2. Frontend (React + Vite)

```bash
cd src/frontend
npm install
npm run dev
```

- **Dashboard UI:** `http://localhost:5173`
