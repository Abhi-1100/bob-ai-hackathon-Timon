# Solution Overview: Sentinel Forge

## What We Built

**Sentinel Forge** is an enterprise-grade, autonomous Threat Intelligence Correlation and Alert Prioritization platform designed to eliminate SOC alert fatigue. It ingests high-volume, multi-source raw security telemetry, automatically reconstructs fragmented events into coherent multi-stage **Attack Chains**, maps behaviors dynamically to the **MITRE ATT&CK Framework**, calculates deterministic 100-point risk scores, generates actionable incident containment recommendations, produces executive **BLUF (Bottom Line Up Front)** intelligence briefings, and provides an interactive, grounded AI Analyst Copilot.

Sentinel Forge is 100% dynamic, features complete multi-tenant tenant isolation, and operates with zero mock or static data fallbacks.

---

## How It Works: End-to-End Pipeline

```
[Raw Security CSV/Feed]
         │
         ▼
[1. Ingestion & Normalization]
    • Validates timestamps, source/destination IPs, event signatures, and severity levels.
    • Deduplicates and purges malformed rows; persists into PostgreSQL under user tenant ID.
         │
         ▼
[2. Rule-Based Alert Correlation Engine]
    • Groups related alerts across temporal windows (30-min threshold) and common source IPs.
    • Reconstructs chronological attack progressions into discrete Attack Chains (e.g., AC001).
         │
         ▼
[3. Automated MITRE ATT&CK Mapping]
    • Matches event signatures to MITRE enterprise tactics and techniques (e.g., T1046, T1110, T1078).
    • Deduplicates tactical mappings and links them to attack chain records in the relational database.
         │
         ▼
[4. Deterministic Risk Scoring Engine]
    • Computes a transparent 0–100 risk score based on:
        - Base event severity weights
        - MITRE tactical progression impact
        - Chain length & multi-stage bonus tiers
    • Classifies incidents into Critical, High, Medium, or Low priority bands.
         │
         ▼
[5. LangGraph Workflow Orchestration & AI Agents]
    • Recommendation Agent (Groq / watsonx.ai): Generates prioritized Immediate, Containment, Investigation, and Prevention actions.
    • BLUF Report Agent: Synthesizes executive briefings with threat levels, affected assets, and strategic conclusions.
         │
         ▼
[6. Vector Knowledge Synchronization (Qdrant)]
    • Generates dense semantic embeddings for all attack chains, risk factors, and MITRE tactics.
    • Indexes vectors into Qdrant for fast, sub-millisecond semantic similarity search.
         │
         ▼
[7. Conversational AI Analyst Copilot & SOC Dashboard]
    • Analysts query the system via natural language (e.g., "What is our highest risk attack chain?").
    • LangGraph multi-turn agent executes grounded RAG queries against Qdrant and relational data with conversational memory.
    • Real-time reactive glassmorphic UI displays live KPIs, interactive charts, matrices, and report downloads.
```

---

## Key Design Decisions

| Decision | Rationale |
| :--- | :--- |
| **Deterministic Multi-Factor Scoring over Pure LLM Scoring** | Relying solely on LLMs for risk scores introduces non-deterministic hallucinations and inconsistencies. Our hybrid architecture calculates mathematical 0–100 scores deterministically, using AI strictly where semantic reasoning excels (synthesis, recommendations, dialogue). |
| **LangGraph Stateful Agent Workflows** | Traditional LLM chains cannot recover from step failures or handle cyclic state transformations. LangGraph allows conditional edge routing, state checkpoints, and robust error recovery. |
| **Two-Tier Caching (L1 Local Memory + L2 Upstash Redis)** | High-concurrency SOC environments execute frequent telemetry reads. Tenant-scoped Redis caching delivers sub-10ms response times while preventing cross-tenant data bleeding. |
| **Dense Vector RAG with Qdrant** | Enables contextual semantic search across enterprise threat memory. Analysts can query using plain English even when their terminology differs from exact database keywords. |
| **Strict Multi-Tenant Database Isolation** | Every upload, alert, chain, report, and chat session is enforced with `user_id` foreign keys and SQLAlchemy query filters, ensuring complete privacy between operators. |

---

## AI Technologies & Integrations

- **watsonx.ai / Groq Llama 3.3 70B Versatile**: Powers autonomous reasoning for tactical recommendation generation, executive BLUF report synthesis, and analyst query understanding.
- **FastEmbed (`BAAI/bge-small-en-v1.5`)**: High-performance local sentence embedding generation (384 dimensions) for Qdrant vector indexing with minimal latency.
- **Qdrant Vector Database**: Cloud and in-memory vector storage enabling cosine-distance similarity search across historical attack chains and threat intelligence documents.
- **LangChain & LangGraph**: State-managed agent graphs coordinating the multi-turn memory node, retrieval node, and synthesis nodes.
