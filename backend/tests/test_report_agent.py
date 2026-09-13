"""
Unit tests for the Executive BLUF Report Generation Agent, Service, and API endpoints.
Uses in-memory SQLite with StaticPool for thread-safe testing.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import (
    Base,
    AttackChainDB,
    MitreMappingDB,
    RiskScoreDB,
    RecommendationDB,
    ReportDB,
)
from database.session import get_db
from main import app
from agents.bluf_report_agent import BlufReportAgent, BlufReportError
from services.report_service import ReportService
from services.risk_scoring import ChainNotFoundError
from repositories.report_repository import ReportRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite DB with all tables for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """TestClient that uses the in-memory SQLite test session."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def _seed_chain(
    session,
    chain_id: str = "AC001",
    events: str = "PortScan,BruteForce,CredentialDumping,Malware",
    source_ip: str = "192.168.1.100",
    destination_ips: str = "10.0.0.5,10.0.0.6",
) -> AttackChainDB:
    """Helper to seed an attack chain record."""
    chain = AttackChainDB(
        id=uuid.uuid4(),
        chain_id=chain_id,
        source_ip=source_ip,
        destination_ips=destination_ips,
        events=events,
        alert_count=len(events.split(",")),
        start_time=datetime(2026, 9, 13, 10, 0, 0),
        end_time=datetime(2026, 9, 13, 10, 30, 0),
    )
    session.add(chain)
    session.commit()
    return chain


def _seed_mitre(session, chain_id: uuid.UUID, technique_id: str, name: str, tactic: str) -> MitreMappingDB:
    """Helper to seed MITRE technique mapping."""
    mapping = MitreMappingDB(
        id=uuid.uuid4(),
        attack_chain_id=chain_id,
        technique_id=technique_id,
        technique_name=name,
        tactic=tactic,
        event="TestEvent",
    )
    session.add(mapping)
    session.commit()
    return mapping


def _seed_risk(session, chain_id: uuid.UUID, score: int = 92, level: str = "Critical") -> RiskScoreDB:
    """Helper to seed a calculated risk score."""
    risk = RiskScoreDB(
        id=uuid.uuid4(),
        attack_chain_id=chain_id,
        score=score,
        level=level,
        reasoning=json.dumps(["Malware activity detected", "Credential theft observed"]),
        event_score=75,
        mitre_score=20,
        chain_bonus=10,
    )
    session.add(risk)
    session.commit()
    return risk


def _seed_recommendation(session, chain_id: uuid.UUID) -> RecommendationDB:
    """Helper to seed a recommendation record."""
    rec = RecommendationDB(
        id=uuid.uuid4(),
        attack_chain_id=chain_id,
        immediate_actions=json.dumps(["Block source IP 192.168.1.100", "Isolate host 10.0.0.5"]),
        containment_actions=json.dumps(["Segment subnet", "Blacklist malware binary"]),
        investigation_actions=json.dumps(["Acquire memory dump", "Review PowerShell logs"]),
        prevention_actions=json.dumps(["Enable Credential Guard", "Enforce MFA"]),
        executive_summary="Critical threat requiring immediate containment.",
    )
    session.add(rec)
    session.commit()
    return rec


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------
class TestBlufReportAgent:

    def test_build_prompts(self):
        """Test system and human prompt construction."""
        agent = BlufReportAgent()
        sys_prompt = agent.build_system_prompt()
        assert "Senior Cyber Threat Intelligence Analyst" in sys_prompt
        assert "executive_summary MUST be under 100 words" in sys_prompt
        assert "Return JSON only" in sys_prompt

        human_prompt = agent.build_human_prompt(
            chain_id="AC001",
            events=["PortScan", "BruteForce", "Malware"],
            source_ip="192.168.1.50",
            destination_ips=["10.0.0.12"],
            mitre_techniques=[{"technique_id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance"}],
            risk_score=92,
            risk_level="Critical",
            reasoning=["Malware activity detected"],
            recommendations={"immediate_actions": ["Block IP"]},
        )
        assert "AC001" in human_prompt
        assert "192.168.1.50" in human_prompt
        assert "10.0.0.12" in human_prompt
        assert "T1595" in human_prompt
        assert "Score: 92 / 100" in human_prompt
        assert "Critical" in human_prompt

    def test_parse_and_validate_clean_json(self):
        """Test parsing valid JSON without formatting anomalies."""
        agent = BlufReportAgent()
        sample_json = json.dumps({
            "chain_id": "AC001",
            "threat_level": "Critical",
            "executive_summary": "Intrusion detected targeting core database host. Immediate isolation required.",
            "attack_overview": "Adversary conducted port scanning followed by credential theft and execution.",
            "affected_assets": "Host 10.0.0.5; Attacker 192.168.1.50.",
            "mitre_summary": "Mapped to T1595, T1110, and T1003.",
            "risk_assessment": "Assessed at 92/100 due to observed credential access.",
            "recommended_actions": "1. Isolate host\n2. Revoke tokens",
            "conclusion": "Incident contained; post-incident review initiated.",
        })
        output = agent.parse_and_validate(sample_json, "AC001", "Critical")
        assert output.chain_id == "AC001"
        assert output.threat_level == "Critical"
        assert len(output.executive_summary) > 10

    def test_parse_and_validate_markdown_fences(self):
        """Test parsing JSON enclosed in markdown code fences."""
        agent = BlufReportAgent()
        fenced = (
            "```json\n"
            "{\n"
            '  "chain_id": "AC002",\n'
            '  "threat_level": "High",\n'
            '  "executive_summary": "High risk activity detected on edge gateway.",\n'
            '  "attack_overview": "Repeated brute-force password guessing against SSH service.",\n'
            '  "affected_assets": "Gateway 10.0.0.1.",\n'
            '  "mitre_summary": "T1110 Brute Force.",\n'
            '  "risk_assessment": "Assessed at 65/100.",\n'
            '  "recommended_actions": "Block IP and enforce fail2ban.",\n'
            '  "conclusion": "Attack thwarted by rate limits."\n'
            "}\n"
            "```"
        )
        output = agent.parse_and_validate(fenced, "AC002", "High")
        assert output.chain_id == "AC002"
        assert output.threat_level == "High"

    def test_parse_and_validate_conversational_filler(self):
        """Test extracting JSON when surrounded by model conversational text."""
        agent = BlufReportAgent()
        conversational = (
            "Here is the executive BLUF report:\n"
            "{\n"
            '  "chain_id": "AC003",\n'
            '  "threat_level": "Medium",\n'
            '  "executive_summary": "Reconnaissance activity observed on perimeter DMZ.",\n'
            '  "attack_overview": "Port scan identified probes on ports 80 and 443.",\n'
            '  "affected_assets": "DMZ Web Server 10.0.1.5.",\n'
            '  "mitre_summary": "T1595 Active Scanning.",\n'
            '  "risk_assessment": "Assessed at 35/100.",\n'
            '  "recommended_actions": "Update firewall deny rules.",\n'
            '  "conclusion": "No breach detected."\n'
            "}\n"
            "End of report."
        )
        output = agent.parse_and_validate(conversational, "AC003", "Medium")
        assert output.chain_id == "AC003"
        assert output.threat_level == "Medium"

    def test_grounded_fallback_generation(self):
        """Test deterministic BLUF report generation when LLM is offline."""
        agent = BlufReportAgent(api_key="")  # Force offline fallback
        output = agent.generate(
            chain_id="AC004",
            events=["PortScan", "BruteForce", "CredentialDumping", "Malware"],
            source_ip="185.220.101.5",
            destination_ips=["10.0.1.25"],
            mitre_techniques=[{"technique_id": "T1003", "name": "Credential Dumping", "tactic": "Credential Access"}],
            risk_score=92,
            risk_level="Critical",
            reasoning=["Credential theft behavior observed", "Malware activity detected"],
        )
        assert output.chain_id == "AC004"
        assert output.threat_level == "Critical"
        assert "185.220.101.5" in output.executive_summary
        assert "10.0.1.25" in output.affected_assets
        assert "T1003" in output.mitre_summary
        assert "92/100" in output.risk_assessment
        assert "Next recommended milestone" in output.conclusion


class TestReportService:

    def test_service_generate_and_persist(self, db_session):
        """Test generating and saving BLUF report to database."""
        chain = _seed_chain(db_session, "AC010", "PortScan,Malware")
        _seed_mitre(db_session, chain.id, "T1595", "Active Scanning", "Reconnaissance")
        _seed_risk(db_session, chain.id, 65, "High")
        _seed_recommendation(db_session, chain.id)

        service = ReportService(db=db_session)
        report, cached = service.generate_report("AC010")

        assert report.chain_id == "AC010"
        assert cached is False
        assert report.threat_level == "High"

        # Verify persisted in database
        repo = ReportRepository(db_session)
        db_rep = repo.get_report(chain.id)
        assert db_rep is not None
        assert db_rep.executive_summary == report.executive_summary
        assert db_rep.threat_level == "High"

    def test_service_caching_behavior(self, db_session):
        """Test second call to generate_report returns cached result."""
        chain = _seed_chain(db_session, "AC011", "PortScan,BruteForce")
        _seed_risk(db_session, chain.id, 45, "Medium")

        service = ReportService(db=db_session)

        # First call: generates
        rep1, cached1 = service.generate_report("AC011")
        assert cached1 is False

        # Second call: cached
        rep2, cached2 = service.generate_report("AC011")
        assert cached2 is True
        assert rep2.chain_id == rep1.chain_id
        assert rep2.executive_summary == rep1.executive_summary

    def test_service_force_refresh_bypasses_cache(self, db_session):
        """Test force_refresh=True bypasses cache."""
        chain = _seed_chain(db_session, "AC012", "PortScan,BruteForce")
        _seed_risk(db_session, chain.id, 45, "Medium")

        service = ReportService(db=db_session)
        _, cached1 = service.generate_report("AC012")
        assert cached1 is False

        # Force refresh
        _, cached_refreshed = service.generate_report("AC012", force_refresh=True)
        assert cached_refreshed is False

    def test_service_auto_resolves_missing_dependencies(self, db_session):
        """Test service auto-calculates risk score and recommendations if missing."""
        chain = _seed_chain(db_session, "AC013", "PortScan,BruteForce,Malware")
        # Do NOT seed risk score or recommendation

        service = ReportService(db=db_session)
        report, _ = service.generate_report("AC013")

        assert report.chain_id == "AC013"
        assert report.threat_level in ["High", "Critical"]

        # Verify risk score was created in DB
        db_risk = db_session.query(RiskScoreDB).filter(RiskScoreDB.attack_chain_id == chain.id).first()
        assert db_risk is not None

        # Verify recommendation was created in DB
        db_rec = db_session.query(RecommendationDB).filter(RecommendationDB.attack_chain_id == chain.id).first()
        assert db_rec is not None

    def test_service_chain_not_found_raises_error(self, db_session):
        """Test non-existent chain raises ChainNotFoundError."""
        service = ReportService(db=db_session)
        with pytest.raises(ChainNotFoundError):
            service.generate_report("NON_EXISTENT_CHAIN")


class TestReportAPI:

    def test_api_generate_report(self, client, db_session):
        """Test POST /api/v1/reports/generate/{chain_id} endpoint."""
        chain = _seed_chain(db_session, "AC020", "PortScan,BruteForce,CredentialDumping,Malware")
        _seed_mitre(db_session, chain.id, "T1110", "Brute Force", "Credential Access")
        _seed_risk(db_session, chain.id, 85, "Critical")

        response = client.post("/api/v1/reports/generate/AC020")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report_generated"] is True
        assert data["chain_id"] == "AC020"
        assert data["cached"] is False
        assert len(data["data"]["executive_summary"]) > 0
        assert data["data"]["threat_level"] == "Critical"

        # Subsequent call returns cached
        repeat_resp = client.post("/api/v1/reports/generate/AC020")
        assert repeat_resp.status_code == 200
        repeat_data = repeat_resp.json()
        assert repeat_data["cached"] is True

    def test_api_generate_report_not_found(self, client):
        """Test POST /api/v1/reports/generate/{chain_id} for unknown chain returns 404."""
        response = client.post("/api/v1/reports/generate/UNKNOWN_CHAIN")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_api_get_report(self, client, db_session):
        """Test GET /api/v1/reports/{chain_id} retrieves stored report."""
        chain = _seed_chain(db_session, "AC021", "PortScan")
        _seed_risk(db_session, chain.id, 20, "Low")

        # Generate first
        client.post("/api/v1/reports/generate/AC021")

        # Now retrieve
        response = client.get("/api/v1/reports/AC021")
        assert response.status_code == 200
        data = response.json()
        assert data["chain_id"] == "AC021"
        assert data["threat_level"] == "Low"
        assert "executive_summary" in data
        assert "conclusion" in data

    def test_api_get_report_not_found_before_generation(self, client, db_session):
        """Test GET /api/v1/reports/{chain_id} before generating returns 404."""
        _seed_chain(db_session, "AC022", "PortScan")

        response = client.get("/api/v1/reports/AC022")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_api_list_all_reports(self, client, db_session):
        """Test GET /api/v1/reports lists all stored reports."""
        _seed_chain(db_session, "AC_REP_1", "PortScan")
        _seed_chain(db_session, "AC_REP_2", "Malware")

        # Generate both
        client.post("/api/v1/reports/generate/AC_REP_1")
        client.post("/api/v1/reports/generate/AC_REP_2")

        response = client.get("/api/v1/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_reports"] == 2
        assert len(data["reports"]) == 2
