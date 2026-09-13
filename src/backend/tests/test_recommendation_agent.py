"""
Unit tests for the LLM Recommendation Agent and Service.
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
)
from database.session import get_db
from main import app
from agents.recommendation_agent import RecommendationAgent, LLMRecommendationError
from services.recommendation_service import RecommendationService
from services.risk_scoring import ChainNotFoundError
from repositories.recommendation_repository import RecommendationRepository


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


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------
class TestRecommendationAgent:

    def test_build_prompts(self):
        """Test system and human prompt construction contain required context."""
        agent = RecommendationAgent()
        sys_prompt = agent.build_system_prompt()
        assert "Senior Cybersecurity Threat Analyst" in sys_prompt
        assert "Containment" in sys_prompt
        assert "Return valid JSON only" in sys_prompt

        human_prompt = agent.build_human_prompt(
            chain_id="AC001",
            events=["PortScan", "BruteForce", "Malware"],
            source_ip="192.168.1.50",
            destination_ips=["10.0.0.12"],
            mitre_techniques=[{"technique_id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance"}],
            risk_score=92,
            risk_level="Critical",
            reasoning=["Malware activity detected"],
        )
        assert "AC001" in human_prompt
        assert "192.168.1.50" in human_prompt
        assert "10.0.0.12" in human_prompt
        assert "T1595" in human_prompt
        assert "92 / 100" in human_prompt
        assert "Critical" in human_prompt

    def test_parse_and_validate_clean_json(self):
        """Test parsing valid JSON without formatting issues."""
        agent = RecommendationAgent()
        sample_json = json.dumps({
            "chain_id": "AC001",
            "immediate_actions": ["Block IP 10.0.0.1", "Isolate endpoint", "Revoke Kerberos tokens"],
            "containment_actions": ["Segment subnet", "Blacklist malware hash", "Disable user account"],
            "investigation_actions": ["Triage memory dump", "Review Event ID 4688", "Analyze network PCAP"],
            "prevention_actions": ["Enable Credential Guard", "Enforce MFA", "Deploy LAPS across servers"],
            "executive_summary": "Intrusion detected and contained promptly with no data loss.",
        })
        output = agent.parse_and_validate(sample_json, "AC001")
        assert output.chain_id == "AC001"
        assert len(output.immediate_actions) == 3
        assert len(output.containment_actions) == 3
        assert len(output.investigation_actions) == 3
        assert len(output.prevention_actions) == 3

    def test_parse_and_validate_markdown_fences(self):
        """Test parsing JSON enclosed in markdown code fences."""
        agent = RecommendationAgent()
        fenced = (
            "```json\n"
            "{\n"
            '  "chain_id": "AC002",\n'
            '  "immediate_actions": ["Block source IP", "Isolate host", "Reset credentials"],\n'
            '  "containment_actions": ["Block port 445", "Quarantine files", "Disable token"],\n'
            '  "investigation_actions": ["Review logs", "Check sandbox", "Examine registry"],\n'
            '  "prevention_actions": ["Patch vulnerability", "Enforce MFA", "Update EDR"],\n'
            '  "executive_summary": "Comprehensive incident response enacted for attack chain AC002."\n'
            "}\n"
            "```"
        )
        output = agent.parse_and_validate(fenced, "AC002")
        assert output.chain_id == "AC002"
        assert len(output.immediate_actions) == 3

    def test_parse_and_validate_conversational_filler(self):
        """Test extracting JSON when surrounded by model conversational text."""
        agent = RecommendationAgent()
        conversational = (
            "Here is the security recommendation for your review:\n"
            "{\n"
            '  "chain_id": "AC003",\n'
            '  "immediate_actions": ["Block source IP", "Isolate host", "Reset credentials"],\n'
            '  "containment_actions": ["Block port 445", "Quarantine files", "Disable token"],\n'
            '  "investigation_actions": ["Review logs", "Check sandbox", "Examine registry"],\n'
            '  "prevention_actions": ["Patch vulnerability", "Enforce MFA", "Update EDR"],\n'
            '  "executive_summary": "Analysis of attack chain AC003 completed with high confidence."\n'
            "}\n"
            "Let me know if you need additional details."
        )
        output = agent.parse_and_validate(conversational, "AC003")
        assert output.chain_id == "AC003"
        assert output.executive_summary.startswith("Analysis")

    def test_grounded_fallback_generation(self):
        """Test deterministic SOC recommendations generation when LLM is offline."""
        agent = RecommendationAgent(api_key="")  # Force offline fallback
        output = agent.generate(
            chain_id="AC004",
            events=["PortScan", "CredentialDumping", "Malware"],
            source_ip="185.220.101.5",
            destination_ips=["10.0.1.25"],
            mitre_techniques=[{"technique_id": "T1003", "name": "OS Credential Dumping", "tactic": "Credential Access"}],
            risk_score=92,
            risk_level="Critical",
            reasoning=["Credential theft behavior observed"],
        )
        assert output.chain_id == "AC004"
        assert len(output.immediate_actions) >= 3
        assert len(output.containment_actions) >= 3
        assert len(output.investigation_actions) >= 3
        assert len(output.prevention_actions) >= 3
        assert "185.220.101.5" in output.immediate_actions[0]
        assert "10.0.1.25" in output.immediate_actions[1]
        assert "Critical" in output.executive_summary


class TestRecommendationService:

    def test_service_generate_and_persist(self, db_session):
        """Test generating and saving recommendations to database."""
        chain = _seed_chain(db_session, "AC010", "PortScan,Malware")
        _seed_mitre(db_session, chain.id, "T1595", "Active Scanning", "Reconnaissance")
        _seed_risk(db_session, chain.id, 65, "High")

        service = RecommendationService(db=db_session)
        rec, cached = service.generate_recommendation("AC010")

        assert rec.chain_id == "AC010"
        assert cached is False
        assert len(rec.immediate_actions) >= 3

        # Verify persisted in database
        repo = RecommendationRepository(db_session)
        db_rec = repo.get_recommendation(chain.id)
        assert db_rec is not None
        assert json.loads(db_rec.immediate_actions) == rec.immediate_actions
        assert db_rec.executive_summary == rec.executive_summary

    def test_service_caching_behavior(self, db_session):
        """Test second call to generate_recommendation returns cached result."""
        chain = _seed_chain(db_session, "AC011", "PortScan,BruteForce")
        _seed_risk(db_session, chain.id, 45, "Medium")

        service = RecommendationService(db=db_session)

        # First call: generates
        rec1, cached1 = service.generate_recommendation("AC011")
        assert cached1 is False

        # Second call: cached
        rec2, cached2 = service.generate_recommendation("AC011")
        assert cached2 is True
        assert rec2.chain_id == rec1.chain_id
        assert rec2.immediate_actions == rec1.immediate_actions

    def test_service_force_refresh_bypasses_cache(self, db_session):
        """Test force_refresh=True forces regeneration even if cached."""
        chain = _seed_chain(db_session, "AC012", "PortScan,BruteForce")
        _seed_risk(db_session, chain.id, 45, "Medium")

        service = RecommendationService(db=db_session)
        _, cached1 = service.generate_recommendation("AC012")
        assert cached1 is False

        # Force refresh
        rec_refreshed, cached_refreshed = service.generate_recommendation("AC012", force_refresh=True)
        assert cached_refreshed is False

    def test_service_auto_calculates_missing_risk_score(self, db_session):
        """Test service auto-calculates risk score if missing before recommendation generation."""
        chain = _seed_chain(db_session, "AC013", "PortScan,BruteForce,Malware")
        # Do NOT seed risk score

        service = RecommendationService(db=db_session)
        rec, _ = service.generate_recommendation("AC013")

        assert rec.chain_id == "AC013"
        # Verify risk score was calculated in DB
        risk_repo = RiskScoreDB
        db_risk = db_session.query(RiskScoreDB).filter(RiskScoreDB.attack_chain_id == chain.id).first()
        assert db_risk is not None
        assert db_risk.score > 0

    def test_service_chain_not_found_raises_error(self, db_session):
        """Test non-existent attack chain raises ChainNotFoundError."""
        service = RecommendationService(db=db_session)
        with pytest.raises(ChainNotFoundError):
            service.generate_recommendation("NON_EXISTENT_CHAIN")


class TestRecommendationAPI:

    def test_api_generate_recommendation(self, client, db_session):
        """Test POST /api/v1/recommendations/generate/{chain_id} endpoint."""
        chain = _seed_chain(db_session, "AC020", "PortScan,BruteForce,Malware")
        _seed_mitre(db_session, chain.id, "T1110", "Brute Force", "Credential Access")
        _seed_risk(db_session, chain.id, 85, "Critical")

        response = client.post("/api/v1/recommendations/generate/AC020")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["recommendation_generated"] is True
        assert data["chain_id"] == "AC020"
        assert data["cached"] is False
        assert len(data["data"]["immediate_actions"]) >= 3
        assert len(data["data"]["containment_actions"]) >= 3
        assert len(data["data"]["investigation_actions"]) >= 3
        assert len(data["data"]["prevention_actions"]) >= 3

        # Repeat request without force_refresh: should return cached=True
        repeat_resp = client.post("/api/v1/recommendations/generate/AC020")
        assert repeat_resp.status_code == 200
        repeat_data = repeat_resp.json()
        assert repeat_data["cached"] is True

    def test_api_generate_recommendation_not_found(self, client):
        """Test POST /api/v1/recommendations/generate/{chain_id} for unknown chain returns 404."""
        response = client.post("/api/v1/recommendations/generate/UNKNOWN_CHAIN")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_api_get_recommendation(self, client, db_session):
        """Test GET /api/v1/recommendations/{chain_id} retrieves stored recommendation."""
        chain = _seed_chain(db_session, "AC021", "PortScan")
        _seed_risk(db_session, chain.id, 20, "Low")

        # Generate first
        client.post("/api/v1/recommendations/generate/AC021")

        # Now retrieve via GET
        response = client.get("/api/v1/recommendations/AC021")
        assert response.status_code == 200
        data = response.json()
        assert data["chain_id"] == "AC021"
        assert len(data["immediate_actions"]) >= 3
        assert "executive_summary" in data

    def test_api_get_recommendation_not_found_before_generation(self, client, db_session):
        """Test GET /api/v1/recommendations/{chain_id} before generating returns 404."""
        _seed_chain(db_session, "AC022", "PortScan")

        response = client.get("/api/v1/recommendations/AC022")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_api_generate_all_recommendations(self, client, db_session):
        """Test POST /api/v1/recommendations/generate-all endpoint."""
        _seed_chain(db_session, "AC_BULK_1", "PortScan")
        _seed_chain(db_session, "AC_BULK_2", "Malware")

        response = client.post("/api/v1/recommendations/generate-all")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_chains"] == 2
        assert len(data["recommendations"]) == 2
