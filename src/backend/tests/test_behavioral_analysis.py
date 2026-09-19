"""
Unit and Integration Tests for Behavioral + Context Analysis Layer.
Validates multi-dimensional anomaly detection, feature extraction, baselining,
scoring explainability, LangGraph workflow node execution, and risk score integration.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import (
    Base,
    AttackChainDB,
    Alert as AlertDB,
    UserDB,
    EntityBaselineDB,
    BehavioralAnalysisDB,
)
from schemas.behavioral import (
    DimensionSignal,
    BehavioralAnalysisResult,
)
from services.behavioral_analysis import (
    BehaviorFeatureExtractor,
    BaselineService,
    AnomalyScorer,
    BehavioralAnalysisEngine,
    BEHAVIOR_WEIGHTS,
)
from services.risk_scoring import RiskScoringEngine
from graph.threat_workflow import create_threat_workflow
from graph.state import ThreatWorkflowState
from nodes.behavior_node import behavior_node

TEST_USER_ID = uuid.UUID("a1b2c3d4-e5f6-4a8b-9c0d-1e2f3a4b5c6d")


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

    user = UserDB(
        id=TEST_USER_ID,
        email="analyst@ThreatIntel.mil",
        full_name="SOC Analyst",
        hashed_password="mock_password",
    )
    session.add(user)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _seed_test_chain(session, chain_id: str = "AC001", source_ip: str = "203.0.113.88", events: str = "PortScan,BruteForce,CredentialDumping,Malware"):
    chain = AttackChainDB(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        chain_id=chain_id,
        source_ip=source_ip,
        destination_ips="10.0.0.5,10.0.0.6,10.0.0.7,10.0.0.8",
        events=events,
        alert_count=len(events.split(",")),
        start_time=datetime(2026, 9, 13, 2, 30, 0, tzinfo=timezone.utc), # Off-hours (02:30 UTC)
        end_time=datetime(2026, 9, 13, 2, 30, 2, tzinfo=timezone.utc),   # 2 seconds -> high burst
    )
    session.add(chain)
    session.commit()
    return chain


# ---------------------------------------------------------------------------
# 1. Schema Validation Tests
# ---------------------------------------------------------------------------
def test_schemas_validation():
    signal = DimensionSignal(
        dimension="network",
        score=75.0,
        signals=["External source IP", "IP address observed for the first time"],
        available=True,
    )
    assert signal.dimension == "network"
    assert signal.score == 75.0
    assert len(signal.signals) == 2
    assert signal.available is True

    result = BehavioralAnalysisResult(
        chain_id="AC001",
        anomaly_score=68.5,
        anomaly_level="High",
        signals=signal.signals,
        dimension_breakdown={"network": signal},
        why_prioritized="High-risk network anomaly detected"
    )
    assert result.chain_id == "AC001"
    assert result.anomaly_score == 68.5
    assert result.anomaly_level == "High"
    assert len(result.signals) == 2


# ---------------------------------------------------------------------------
# 2. Feature Extractor Validation
# ---------------------------------------------------------------------------
def test_feature_extractor(db_session):
    chain = _seed_test_chain(db_session, chain_id="AC_FEAT_01")
    features = BehaviorFeatureExtractor.extract_features(chain, [])

    assert features["source_ip"] == "203.0.113.88"
    assert len(features["destination_ips"]) == 4
    assert len(features["events"]) == 4
    assert features["is_working_hours"] is False  # 02:30 is outside 8..18
    assert features["velocity_alerts_per_second"] == 2.0  # 4 alerts / 2 seconds


# ---------------------------------------------------------------------------
# 3. Time Dimension Anomaly Scoring
# ---------------------------------------------------------------------------
def test_time_dimension_scoring():
    # Outside working hours
    sig_off_hours = AnomalyScorer.score_time({"is_working_hours": False}, {})
    assert sig_off_hours.score == 30.0
    assert "Activity outside normal business hours" in sig_off_hours.signals

    # During normal business hours
    sig_normal = AnomalyScorer.score_time({"is_working_hours": True}, {})
    assert sig_normal.score == 0.0
    assert len(sig_normal.signals) == 0


# ---------------------------------------------------------------------------
# 4. Network Dimension Anomaly Scoring (Public vs Private)
# ---------------------------------------------------------------------------
def test_network_dimension_scoring():
    # External unknown IP
    sig_ext = AnomalyScorer.score_network({"source_ip": "203.0.113.50"}, {"is_first_seen_ip": True})
    assert sig_ext.score == 50.0  # 20 (external) + 30 (first-seen)
    assert "External source IP" in sig_ext.signals
    assert "IP address observed for the first time" in sig_ext.signals

    # Internal known IP
    sig_int = AnomalyScorer.score_network({"source_ip": "10.0.0.5"}, {"is_first_seen_ip": False})
    assert sig_int.score == 0.0
    assert len(sig_int.signals) == 0


# ---------------------------------------------------------------------------
# 5. Target Dimension Anomaly Scoring
# ---------------------------------------------------------------------------
def test_target_dimension_scoring():
    # Multiple unknown targets
    features = {"destination_ips": ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"]}
    context = {"is_known_target": False}
    sig = AnomalyScorer.score_target(features, context)
    assert sig.score == 60.0  # 40 (unknown) + 20 (multiple targets > 3)
    assert "First-time access to target resource(s)" in sig.signals
    assert "Multiple targets accessed (4)" in sig.signals


# ---------------------------------------------------------------------------
# 6. Behavior Velocity Anomaly Scoring
# ---------------------------------------------------------------------------
def test_behavior_velocity_scoring():
    # Rapid burst
    features = {
        "velocity_alerts_per_second": 15.0,
        "events": ["PortScan", "BruteForce", "CredentialDumping", "Malware"],
    }
    sig = AnomalyScorer.score_behavior(features, {})
    assert sig.score == 80.0  # 60 (burst > 10) + 20 (unique events > 3)
    assert "High-velocity burst activity" in sig.signals
    assert "High diversity of security events" in sig.signals


# ---------------------------------------------------------------------------
# 7. Baseline Service Context Retrieval
# ---------------------------------------------------------------------------
def test_baseline_service(db_session):
    baseline_svc = BaselineService(db=db_session)
    features = {"source_ip": "198.51.100.5"}
    context = baseline_svc.get_baseline_context(TEST_USER_ID, features)

    assert context["is_first_seen_ip"] is True
    assert context["is_known_target"] is False


# ---------------------------------------------------------------------------
# 8. Anomaly Scorer Aggregation & Explainability
# ---------------------------------------------------------------------------
def test_anomaly_scorer_aggregation():
    dimensions = {
        "identity": DimensionSignal(dimension="identity", score=0.0, signals=[], available=False),
        "device": DimensionSignal(dimension="device", score=0.0, signals=[], available=False),
        "network": DimensionSignal(dimension="network", score=50.0, signals=["External source IP"], available=True),
        "target": DimensionSignal(dimension="target", score=60.0, signals=["First-time access"], available=True),
        "behavior": DimensionSignal(dimension="behavior", score=80.0, signals=["High-velocity burst activity"], available=True),
        "time": DimensionSignal(dimension="time", score=30.0, signals=["Activity outside normal business hours"], available=True),
        "history": DimensionSignal(dimension="history", score=20.0, signals=["No baseline"], available=True),
        "relationship": DimensionSignal(dimension="relationship", score=30.0, signals=["Novel relationship"], available=True),
    }
    score, level, signals, rationale = AnomalyScorer.calculate_total_anomaly(dimensions)
    assert 25.0 <= score <= 50.0
    assert level in ("Low", "Elevated")
    assert len(signals) > 0
    assert rationale is not None


# ---------------------------------------------------------------------------
# 9. Behavioral Analysis Engine Full Execution & DB Persistence
# ---------------------------------------------------------------------------
def test_engine_analyze_chain_and_persistence(db_session):
    chain = _seed_test_chain(db_session, chain_id="AC_BEHAVE_01")
    engine = BehavioralAnalysisEngine(db=db_session)
    result = engine.analyze_chain("AC_BEHAVE_01", user_id=TEST_USER_ID, persist=True)

    assert result.chain_id == "AC_BEHAVE_01"
    assert result.anomaly_score > 0
    assert len(result.signals) > 0
    assert result.why_prioritized is not None

    # Verify persisted in database
    db_rec = db_session.query(BehavioralAnalysisDB).filter_by(attack_chain_id=chain.id).first()
    assert db_rec is not None
    assert db_rec.anomaly_score == int(round(result.anomaly_score))
    assert db_rec.anomaly_level == result.anomaly_level


# ---------------------------------------------------------------------------
# 10. LangGraph behavior_node Workflow Step
# ---------------------------------------------------------------------------
def test_langgraph_behavior_node(db_session):
    chain = _seed_test_chain(db_session, chain_id="AC_GRAPH_01")
    state: ThreatWorkflowState = {
        "chain_id": "AC_GRAPH_01",
        "user_id": str(TEST_USER_ID),
        "_db": db_session,
        "_user_id": TEST_USER_ID,
        "status": "in_progress",
        "errors": [],
    }

    updated_state = behavior_node(state)
    assert "behavioral_analysis" in updated_state
    b_analysis = updated_state["behavioral_analysis"]
    assert b_analysis is not None
    assert b_analysis["chain_id"] == "AC_GRAPH_01"
    assert "anomaly_score" in b_analysis
    assert "anomaly_level" in b_analysis


# ---------------------------------------------------------------------------
# 11. Additive Risk Score Integration
# ---------------------------------------------------------------------------
def test_additive_risk_score_integration(db_session):
    chain = _seed_test_chain(db_session, chain_id="AC_RISK_01", events="PortScan,BruteForce")

    risk_engine = RiskScoringEngine(db=db_session)
    
    # 1. Without behavioral score
    score_clean = risk_engine.score_chain_data(
        chain_id="AC_RISK_01",
        events=["PortScan", "BruteForce"]
    )
    # PortScan(10) + BruteForce(25) = 35
    assert score_clean.score == 35
    assert score_clean.behavioral_score is None

    # 2. With behavioral score (80/100 -> +20 additive points capped at 25)
    score_elevated = risk_engine.score_chain_data(
        chain_id="AC_RISK_01",
        events=["PortScan", "BruteForce"],
        behavioral_score=80,
        behavioral_level="High",
        behavioral_reasons=["External source IP targeting internal critical resources"]
    )
    # 35 + round(80/100 * 25) = 35 + 20 = 55
    assert score_elevated.score == 55
    assert score_elevated.level == "High"
    assert score_elevated.behavioral_score == 80
    assert any("Contextual behavioral analysis" in r for r in score_elevated.reasoning)
    assert any("External source IP" in r for r in score_elevated.reasoning)
