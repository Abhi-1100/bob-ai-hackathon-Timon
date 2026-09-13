# 🚀 TimonTrack

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

> See [`docs/problem-statement.md`](docs/problem-statement.md) for the full problem statement.

[Describe the real-world problem your project addresses. Be specific about who the user is and what pain point they face.]

---

## 💡 Solution

> See [`docs/solution-overview.md`](docs/solution-overview.md) for the full solution overview.

[Describe your solution clearly. Explain the core mechanism — what makes it work.]

---

## ✨ Key Features

- **Feature 1:** [Brief description — e.g., "Real-time anomaly detection using watsonx.ai"]
- **Feature 2:** [Brief description]
- **Feature 3:** [Brief description]
- **Feature 4:** [Optional]
- **Feature 5:** [Optional]

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | [e.g., Python, TypeScript] |
| **Frameworks** | [e.g., FastAPI, React] |
| **IBM Technologies** | [e.g., watsonx.ai, IBM Bob, IBM Cloud] |
| **Databases** | [e.g., PostgreSQL, Redis] |
| **Other** | [e.g., Docker, GitHub Actions] |

---

## 📁 Repository Structure

```
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your [`docs/setup-guide.md`](docs/setup-guide.md)**

```bash
# 1. Clone the repo
git clone https://github.com/Abhi-1100/bob-ai-hackathon-Timon.git
cd bob-ai-hackathon-Timon

# 2. Install dependencies
[your install command here]

# 3. Configure environment
cp src/.env.example src/.env
# Edit .env with your values

# 4. Run the project
[your run command here]
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

> Be honest — judges appreciate transparency over overclaiming.

- [Limitation 1: e.g., "Authentication is mocked — not production-ready"]
- [Limitation 2: e.g., "Only tested on Chrome"]
- [Limitation 3: e.g., "Feature X is scaffolded but not fully implemented"]

---

## 🏅 What We're Most Proud Of

[Tell the judges what part of your submission is strongest and worth paying close attention to.]

---

## 🔗 Repository

[https://github.com/Abhi-1100/bob-ai-hackathon-Timon](https://github.com/Abhi-1100/bob-ai-hackathon-Timon)
# Sentinel Forge frontend

React/Vite frontend for the Threat Intelligence Correlation & Alert Prioritisation Assistant.

Frontend source lives under `src/frontend/`; `index.html` loads `src/frontend/main.jsx` as the Vite entry point.

## Run locally

```powershell
npm.cmd install
npm.cmd run dev
```

The frontend uses `http://localhost:8000` by default. To point it at another FastAPI instance, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

The UI intentionally renders empty and error states when the API has no data; it does not seed fabricated threat records.
