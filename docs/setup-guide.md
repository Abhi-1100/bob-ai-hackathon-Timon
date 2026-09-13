# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [x] Python 3.11+
- [x] Node.js 18+ and npm
- [x] Git
- [x] (Optional) Docker Desktop / PostgreSQL / Qdrant instance

## Environment Variables

Copy `.env.example` to `.env` and configure the values:

```bash
cp .env.example .env
```

| Variable | Description | Required | Default |
|---|---|---|---|
| `VITE_API_BASE_URL` | Base URL of the backend API for frontend | Yes | `http://localhost:8000` |
| `DATABASE_URL` | PostgreSQL or SQLite database connection string | No (SQLite fallback) | `sqlite:///./threat_intel.db` |
| `GROQ_API_KEY` | Groq Cloud API key for Llama 3.3 70B inference | Recommended | `""` |
| `WATSONX_API_KEY` | IBM watsonx.ai API key | Optional | `""` |
| `WATSONX_PROJECT_ID` | IBM watsonx.ai project ID | Optional | `""` |
| `QDRANT_URL` | Qdrant Vector database URL (leave empty for in-memory) | No | `""` |
| `QDRANT_API_KEY` | Qdrant API key | No | `""` |

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Abhi-1100/bob-ai-hackathon-Timon.git
cd bob-ai-hackathon-Timon

# 2. Install backend dependencies
pip install -r src/backend/requirements.txt

# 3. Install frontend dependencies
npm install
# Or: cd src/frontend && npm install
```

## Running the Application

```bash
# Start the backend (from repository root)
python main.py
# Or: uvicorn main:app --reload

# Start the frontend (in a separate terminal)
npm run dev
# Or: cd src/frontend && npm run dev
```

- Backend API: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Frontend SOC Dashboard: `http://localhost:5173`

## Running Tests

```bash
# Run the entire backend test suite
python -m pytest src/backend/tests -v
```

## Quick Demo

To ingest sample threat alert data and test the correlation pipeline:

```bash
# Upload sample threat alerts via API
curl -X POST "http://localhost:8000/api/v1/upload/csv" -F "file=@sample_data/enterprise_threat_alerts_1000.csv"

# Run end-to-end threat correlation workflow
curl -X POST "http://localhost:8000/api/v1/workflow/run"
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` | Ensure you installed backend dependencies: `pip install -r src/backend/requirements.txt` |
| Port 8000 already in use | Run uvicorn on another port: `uvicorn main:app --port 8080 --reload` and update `VITE_API_BASE_URL` |
| Qdrant in-memory mode warning | In-memory Qdrant operates automatically when `QDRANT_URL` is empty; no action required |
