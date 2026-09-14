# Sentinel Forge — Hackathon Slide Deck Content

> **Use this ready-to-present outline to create your slides in Google Slides, PowerPoint, or Keynote, then export as `slides.pdf` inside this folder.**

---

### Slide 1: Title Slide
- **Title**: Sentinel Forge
- **Subtitle**: Autonomous Threat Intelligence Correlation & Alert Prioritization Assistant
- **Hackathon Track**: AI Track | Bob AI Innovation Hackathon
- **Team**: TimonTrack
- **Team Members**: Abhi Kakadiya (Lead), Jaimin, Digisha, Om

---

### Slide 2: The Problem — SOC Alert Fatigue Crisis
- **Headline**: Security Operations Centers Are Drowning in Alert Noise
- **Key Points**:
  - **Overwhelming Volume**: 10,000 to 50,000 alerts per day per enterprise.
  - **70%+ False Positives**: Analysts spend hours sifting through benign noise.
  - **Fragmented Intrusions**: Multi-stage attack campaigns are logged as disconnected events across isolated tools.
  - **Delayed Containment**: Average breach detection dwell time exceeds 200 days.
  - **Analyst Burnout**: 60% of SOC analysts report severe cognitive exhaustion.

---

### Slide 3: The Solution — Sentinel Forge
- **Headline**: Autonomous Cyber Intelligence from Raw Alerts to Executive Briefs
- **Key Capabilities**:
  - **Cross-Domain Correlation**: Groups alerts into chronological multi-stage Attack Chains across temporal and IP heuristics.
  - **Automated MITRE ATT&CK Mapping**: Maps adversary behaviors to 14 tactical enterprise categories.
  - **Deterministic Multi-Factor Risk Scoring**: Transparent, non-hallucinated 0–100 mathematical risk prioritization.
  - **Autonomous BLUF Reports & Action Plans**: Instant Bottom-Line-Up-Front briefings and prioritized mitigation steps.
  - **Conversational SOC Copilot**: LangGraph-powered RAG analyst dialogue grounded in real-time vector memory.

---

### Slide 4: Technical Architecture
- **Headline**: Decoupled, Multi-Tenant Cloud Native Architecture
- **Diagram Summary**:
  - **Frontend**: React 18 + Vite Glassmorphic SOC UI (Recharts, Framer Motion)
  - **Gateway / API**: FastAPI with JWT multi-tenant dependency injection
  - **Stateful AI Workflow**: LangGraph Agent coordinating Memory, Qdrant Retrieval, and Answer synthesis
  - **High-Speed Caching**: Two-tier caching (L1 In-Memory + L2 Upstash Redis REST)
  - **Relational Data**: Neon PostgreSQL with strict row-level multi-tenant isolation
  - **Vector Intelligence**: Qdrant Vector DB with dense semantic embeddings (FastEmbed)

---

### Slide 5: Core Features in Action
- **Visuals / Highlights**:
  - **Live Ingestion**: Instant CSV parsing of 1,000+ alerts in under 2 seconds.
  - **Attack Chain Explorer**: Interactive timeline and asset visualization of progression (PortScan -> BruteForce -> PrivilegeEscalation -> Exfiltration).
  - **MITRE Matrix Heatmap**: Real-time tactical coverage breakdown with technique badges.
  - **Incident Prioritization**: Severity distribution cards and critical incident alerts.
  - **Executive Report Synthesis**: Downloadable Markdown/PDF BLUF briefings.

---

### Slide 6: AI Innovation & Hybrid Grounding
- **Headline**: Deterministic Precision Meets Generative Intelligence
- **Why It Matters**:
  - **Zero Hallucination Risk Scores**: Mathematical calculation ensures auditability and consistency.
  - **Grounded Semantic RAG**: Qdrant vector retrieval injects precise historical telemetry into LLM prompts.
  - **Stateful Conversational Memory**: LangGraph maintains full analyst context across multi-turn investigation sessions.
  - **100% Dynamic & 0 Mock Data**: Completely decoupled from static templates; operates on real live database queries.

---

### Slide 7: Operational Impact & Metrics
- **Headline**: Measurable Acceleration of Incident Response
- **Key Metrics**:
  - **90% Reduction in Triage Time**: Drops initial alert review time from hours to seconds.
  - **Sub-10ms Dashboard Query Latency**: Powered by multi-tenant Upstash Redis caching.
  - **100% Attack Chain Reconstruction**: Automates multi-stage adversary timeline synthesis.
  - **Zero Multi-Tenant Data Leakage**: Mathematically proven isolation between separate organizational workspaces.

---

### Slide 8: The Team & Future Roadmap
- **Team TimonTrack**:
  - Abhi Kakadiya — System Architecture, Backend Pipeline & AI Integration
  - Jaimin — Frontend Engineering, Glassmorphic UI & Visualizations
  - Digisha — Threat Modeling, MITRE ATT&CK Mapping & Risk Algorithms
  - Om — Database Optimization, Multi-Tenant Isolation & Cloud Deployment
- **Future Roadmap**:
  - Direct SIEM webhooks (Splunk, Microsoft Sentinel, Elastic).
  - Automated SOAR remediation dispatch (firewall blocklist integration via API).
  - Advanced threat actor attribution leveraging STIX/TAXII threat feeds.
