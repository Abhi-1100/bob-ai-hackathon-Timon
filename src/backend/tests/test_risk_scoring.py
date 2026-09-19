"""
Unit tests for the Risk Scoring Engine.
Uses an in-memory SQLite database to avoid requiring a live PostgreSQL instance.
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

from database.models import Base, AttackChainDB, MitreMappingDB, RiskScoreDB
from database.session import get_db
from main import app
from services.risk_scoring import (
    RiskScoringEngine,
    ChainNotFoundError,
    EVENT_WEIGHTS,
    MITRE_TACTIC_WEIGHTS,
)
from repositories.risk_repository import RiskRepository


TEST_USER_ID = uuid.UUID("a1b2c3d4-e5f6-4a8b-9c0d-1e2f3a4b5c6d")

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

    from database.models import UserDB
    user = UserDB(
        id=TEST_USER_ID,
        email="analyst@ThreatIntel.mil",
        full_name="Chief SOC Analyst",
        hashed_password="mock_hashed_password",
    )
    session.add(user)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """TestClient that uses the in-memory SQLite test session with mocked auth."""
    from routers.auth import get_current_user_obj
    from database.models import UserDB

    user = db_session.query(UserDB).filter_by(id=TEST_USER_ID).first()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_obj] = lambda: user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def _create_chain(session, chain_id: str, events: str, source_ip: str = "10.0.0.1", user_id: uuid.UUID = TEST_USER_ID) -> AttackChainDB:
    """Helper to seed an attack chain record."""
    chain = AttackChainDB(
        id=uuid.uuid4(),
        user_id=user_id,
        chain_id=chain_id,
        source_ip=source_ip,
        destination_ips="10.0.0.5",
        events=events,
        alert_count=len(events.split(",")),
        start_time=datetime(2026, 9, 13, 10, 0, 0),
        end_time=datetime(2026, 9, 13, 10, 30, 0),
    )
    session.add(chain)
    session.commit()
    return chain


def _create_mitre_mapping(session, chain_id: uuid.UUID, technique_id: str, name: str, tactic: str) -> MitreMappingDB:
    """Helper to seed a MITRE mapping record."""
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


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------
class TestRiskScoringEngine:

    def test_event_score_calculation(self, db_session):
        """Test event score calculation matches expected weights."""
        engine = RiskScoringEngine(db=db_session)
        events = ["PortScan", "BruteForce", "CredentialDumping", "Malware"]
        score, explanations = engine.calculate_event_score(events)

        # 10 + 25 + 40 + 50 = 125
        assert score == 125
        assert any("Malware activity detected" in e for e in explanations)
        assert any("Credential theft behavior observed" in e for e in explanations)

    def test_mitre_score_calculation(self, db_session):
        """Test MITRE tactic weights calculation."""
        engine = RiskScoringEngine(db=db_session)
        mappings = [
            {"tactic": "Reconnaissance"},       # +5
            {"tactic": "Credential Access"},    # +20
            {"tactic": "Exfiltration"},         # +30
        ]
        score, explanations = engine.calculate_mitre_score(mappings)
        # 5 + 20 + 30 = 55
        assert score == 55
        assert any("Exfiltration" in e for e in explanations)
        assert any("Credential Access" in e for e in explanations)

    def test_chain_bonus_tiers(self, db_session):
        """Test progression bonus for chain length."""
        engine = RiskScoringEngine(db=db_session)
        assert engine.calculate_chain_bonus(1) == 0
        assert engine.calculate_chain_bonus(2) == 0
        assert engine.calculate_chain_bonus(3) == 10
        assert engine.calculate_chain_bonus(4) == 10
        assert engine.calculate_chain_bonus(5) == 15
        assert engine.calculate_chain_bonus(6) == 15
        assert engine.calculate_chain_bonus(7) == 20
        assert engine.calculate_chain_bonus(10) == 20

    def test_score_capped_at_100(self, db_session):
        """Verify score never exceeds 100 even with high weights."""
        engine = RiskScoringEngine(db=db_session)
        capped = engine.calculate_total_score(125, 40, 20)
        assert capped == 100

    def test_severity_levels(self, db_session):
        """Verify score to severity level mapping."""
        engine = RiskScoringEngine(db=db_session)
        assert engine.determine_severity(0) == "Low"
        assert engine.determine_severity(25) == "Low"
        assert engine.determine_severity(26) == "Medium"
        assert engine.determine_severity(50) == "Medium"
        assert engine.determine_severity(51) == "High"
        assert engine.determine_severity(75) == "High"
        assert engine.determine_severity(76) == "Critical"
        assert engine.determine_severity(100) == "Critical"

    def test_score_chain_data_standalone_example(self, db_session):
        """Test the exact example from the prompt: PortScan + BruteForce + CredentialDumping + Malware = 100, Critical."""
        engine = RiskScoringEngine(db=db_session)
        events = ["PortScan", "BruteForce", "CredentialDumping", "Malware"]
        result = engine.score_chain_data(chain_id="AC001", events=events)

        assert result.chain_id == "AC001"
        assert result.score == 100
        assert result.level == "Critical"
        assert len(result.reasoning) > 0
        assert result.chain_bonus == 10  # 4 events >= 3

    def test_calculate_and_store_for_chain(self, db_session):
        """Test calculating and persisting a risk score with linked MITRE mappings."""
        chain = _create_chain(db_session, "AC100", "PortScan,BruteForce")
        _create_mitre_mapping(db_session, chain.id, "T1595", "Active Scanning", "Reconnaissance")
        _create_mitre_mapping(db_session, chain.id, "T1110", "Brute Force", "Credential Access")

        engine = RiskScoringEngine(db=db_session)
        score_obj = engine.calculate_and_store_for_chain("AC100")

        assert score_obj.chain_id == "AC100"
        # PortScan(10) + BruteForce(25) = 35
        # Reconnaissance(5) + Credential Access(20) = 25
        # Chain bonus = 0 (2 events)
        # Total = 60 -> High
        assert score_obj.score == 60
        assert score_obj.level == "High"

        # Verify persisted in database
        repo = RiskRepository(db_session)
        db_score = repo.get_by_chain_id(chain.id)
        assert db_score is not None
        assert db_score.score == 60
        assert db_score.level == "High"

    def test_chain_not_found_raises_error(self, db_session):
        """Test scoring a non-existent chain raises ChainNotFoundError."""
        engine = RiskScoringEngine(db=db_session)
        with pytest.raises(ChainNotFoundError):
            engine.calculate_and_store_for_chain("NON_EXISTENT")

    def test_score_all_chains_prioritized_descending(self, db_session):
        """Test bulk scoring sorts attack chains with highest risk first."""
        # Low risk chain
        _create_chain(db_session, "AC_LOW", "PortScan")
        # Critical risk chain
        _create_chain(db_session, "AC_CRIT", "PortScan,BruteForce,CredentialDumping,Malware,DataExfiltration")

        engine = RiskScoringEngine(db=db_session)
        scored = engine.score_all_chains()

        assert len(scored) == 2
        assert scored[0].chain_id == "AC_CRIT"
        assert scored[0].score >= scored[1].score
        assert scored[0].level == "Critical"

    def test_risk_distribution(self, db_session):
        """Test aggregate risk level distribution calculation."""
        _create_chain(db_session, "AC_1", "PortScan")
        _create_chain(db_session, "AC_2", "PortScan,Malware,DataExfiltration")

        engine = RiskScoringEngine(db=db_session)
        engine.score_all_chains()

        dist = engine.get_risk_distribution()
        assert dist.total_chains == 2
        assert dist.low + dist.medium + dist.high + dist.critical == 2

    # -----------------------------------------------------------------------
    # API Endpoint Tests
    # -----------------------------------------------------------------------
    def test_api_calculate_chain_risk(self, client, db_session):
        """Test POST /api/v1/risk/calculate/{chain_id} endpoint."""
        _create_chain(db_session, "AC001", "PortScan,BruteForce,CredentialDumping,Malware")

        response = client.post("/api/v1/risk/calculate/AC001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chain_id"] == "AC001"
        assert data["score"] == 100
        assert data["level"] == "Critical"
        assert len(data["reasoning"]) > 0

    def test_api_calculate_chain_not_found(self, client):
        """Test POST /api/v1/risk/calculate/{chain_id} with invalid ID returns 404."""
        response = client.post("/api/v1/risk/calculate/AC_MISSING")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_api_get_chain_risk(self, client, db_session):
        """Test GET /api/v1/risk/{chain_id} retrieves stored score."""
        _create_chain(db_session, "AC002", "PortScan,BruteForce")

        # First calculate
        client.post("/api/v1/risk/calculate/AC002")

        # Now fetch
        response = client.get("/api/v1/risk/AC002")
        assert response.status_code == 200
        data = response.json()
        assert data["chain_id"] == "AC002"
        assert "score" in data
        assert "level" in data
        assert len(data["reasoning"]) > 0

    def test_api_calculate_all_and_distribution(self, client, db_session):
        """Test POST /api/v1/risk/calculate-all and GET /api/v1/risk/summary/distribution."""
        _create_chain(db_session, "AC_A", "PortScan")
        _create_chain(db_session, "AC_B", "Malware,DataExfiltration")

        calc_resp = client.post("/api/v1/risk/calculate-all")
        assert calc_resp.status_code == 200
        calc_data = calc_resp.json()
        assert calc_data["success"] is True
        assert calc_data["chains_scored"] == 2

        dist_resp = client.get("/api/v1/risk/summary/distribution")
        assert dist_resp.status_code == 200
        dist_data = dist_resp.json()
        assert dist_data["total_chains"] == 2
