# Setup & Deployment Guide: ThreatIntel

> **This file is read by the automated evaluation pipeline and human judges. Follow these steps to run ThreatIntel locally or deploy to cloud providers.**

---

## Prerequisites

Before you begin, ensure you have the following installed:

- [x] **Python 3.11+**
- [x] **Node.js 18+ and npm**
- [x] **Git**
- [x] (Recommended) A **Neon PostgreSQL** database or local PostgreSQL instance
- [x] (Recommended) A **Groq Cloud API Key** (free tier available at [console.groq.com](https://console.groq.com/)) for high-speed Llama 3.3 70B inference
- [x] (Optional) **Upstash Redis** REST URL and Token for distributed caching ([console.upstash.com](https://console.upstash.com/))
- [x] (Optional) **Qdrant Cloud** cluster URL and Key ([cloud.qdrant.io](https://cloud.qdrant.io/)) — falls back to automatic in-memory mode if omitted

---

## Environment Variables Configuration

Copy the template from `src/.env.example` into a `.env` file at the root or inside `src/backend/`:

```bash
cp src/.env.example .env
```

| Variable | Description | Required | Default / Example |
| :--- | :--- | :---: | :--- |
| `DATABASE_URL` | PostgreSQL or SQLite database connection string | Yes | `postgresql+psycopg2://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `GROQ_API_KEY` | Groq Cloud API key for Llama 3.3 70B reasoning | Yes | `gsk_...` |
| `JWT_SECRET` | Secret key for signing authentication tokens | Yes | `your-secure-jwt-secret-key` |
| `VITE_API_BASE_URL` | Backend API base URL consumed by the frontend | Yes | `http://localhost:8000` |
| `UPSTASH_REDIS_REST_URL` | Upstash Redis REST endpoint for L2 caching | Optional | `https://your-db.upstash.io` |
| `UPSTASH_REDIS_REST_TOKEN`| Upstash Redis REST access token | Optional | `your-token` |
| `QDRANT_URL` | Qdrant Vector database URL (leave blank for in-memory) | Optional | `https://your-cluster.cloud.qdrant.io:6333` |
| `QDRANT_API_KEY` | Qdrant API key | Optional | `your-qdrant-key` |
| `WATSONX_API_KEY` | IBM watsonx.ai API key | Optional | `""` |
| `WATSONX_PROJECT_ID` | IBM watsonx.ai project ID | Optional | `""` |

---

## Local Development Setup

### 1. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd src/backend

# (Optional) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
# or: .venv\Scripts\activate # Windows

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Docs (Swagger UI):** `http://127.0.0.1:8000/docs`
- **Health Check Endpoint:** `http://127.0.0.1:8000/health`

### 2. Frontend Setup (React + Vite)

Open a new terminal window:

```bash
# Navigate to frontend directory
cd src/frontend

# Install node dependencies
npm install

# Start the Vite development server
npm run dev
```

- **SOC Web Dashboard:** Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

From the repository root:

```bash
# Run all backend unit and integration tests
pytest src/backend/tests/ -v

# Run the live multi-tenant isolation end-to-end test
pytest src/backend/tests/test_multi_tenant_isolation.py -v -s

# Run frontend production build test
npm --prefix src/frontend run build
```

---

## Cloud Deployment Guide

### A. Deploying Backend to Render
1. Push repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Web Service**.
3. Select your repository.
4. Set configurations:
   - **Root Directory**: `src/backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add the values from your `.env` (`DATABASE_URL`, `GROQ_API_KEY`, `JWT_SECRET`, `UPSTASH_REDIS_REST_URL`, etc.).
6. Click **Deploy Web Service** and copy the live URL (e.g., `https://threat-intel-backend.onrender.com`).

### B. Deploying Frontend to Vercel
1. In [Vercel Dashboard](https://vercel.com/), click **Add New...** -> **Project**.
2. Import your GitHub repository.
3. Set configurations:
   - **Root Directory**: `src/frontend`
   - **Framework Preset**: `Vite`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://threat-intel-backend.onrender.com` (your Render backend URL)
5. Click **Deploy**. Vercel will build the production bundle and serve the live app with SPA routing rewrites.
