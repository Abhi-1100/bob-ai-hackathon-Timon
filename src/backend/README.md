# Threat Intelligence Correlation & Alert Prioritisation Assistant — Backend Source

This directory contains the complete backend service for the **D2: Threat Intelligence Correlation & Alert Prioritisation Assistant**.

Please refer to the primary repository [README.md](../../README.md) for full architectural diagrams, API specifications, and setup instructions.

## Quick Run

```bash
# From this directory:
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Structure
- `app/api/v1/`: Endpoints for alert ingestion, correlation, MITRE ATT&CK mapping, and BLUF generation.
- `app/core/`: Configuration, settings, and security.
- `app/models/`: Pydantic models for alerts, correlated incidents, and BLUF summaries.
- `app/services/`: Core logic for multi-source ingestion, correlation engine, MITRE mapper, and IBM watsonx / Bob BLUF generator.
- `app/data/`: MITRE ATT&CK enterprise datasets and sample feed payloads (SIEM, satellite, sensor).
- `tests/`: Automated test suite.
