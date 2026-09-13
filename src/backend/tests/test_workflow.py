"""
Unit tests for the LangGraph Threat Intelligence Workflow Orchestrator.
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
from graph.threat_workflow import (
    compiled_threat_workflow,
    create_threat_workflow,
    ThreatWorkflowRunner,
)
from graph.state import ThreatWorkflowState
from repositories.attack_chain_repository import AttackChainRepository


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


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------
class TestThreatWorkflowGraph:

    def test_workflow_graph_structure(self):
        """Verify the LangGraph StateGraph compiles with all required nodes."""
        graph = create_threat_workflow()
        assert graph is not None
        # Verify compiled graph has the required nodes
        node_names = set(graph.nodes.keys())
        expected_nodes = {
            "load_chain",
            "mitre_mapping",
            "risk_scoring",
            "recommendations",
            "bluf_report",
            "store_results",
        }
        for node in expected_nodes:
            assert node in node_names, f"Node '{node}' missing from StateGraph"

    def test_workflow_run_end_to_end_success(self, db_session):
        """Test full orchestration workflow execution for a valid attack chain."""
        chain = _seed_chain(db_session, "AC_WF_1", "PortScan,BruteForce,Malware")

        runner = ThreatWorkflowRunner(db=db_session)
        final_state = runner.run("AC_WF_1")

        assert final_state["status"] == "completed"
        assert len(final_state["errors"]) == 0

        # Verify all node outputs are populated in state
        assert final_state["attack_chain"] is not None
        assert final_state["attack_chain"]["chain_id"] == "AC_WF_1"

        assert final_state["mitre_mappings"] is not None
        assert len(final_state["mitre_mappings"]) > 0

        assert final_state["risk_score"] is not None
        assert final_state["risk_score"]["score"] > 0
        assert final_state["risk_score"]["level"] in ["Medium", "High", "Critical"]

        assert final_state["recommendations"] is not None
        assert len(final_state["recommendations"]["immediate_actions"]) >= 3

        assert final_state["report"] is not None
        assert "executive_summary" in final_state["report"]

        # Verify database persistence
        assert db_session.query(MitreMappingDB).filter_by(attack_chain_id=chain.id).count() > 0
        assert db_session.query(RiskScoreDB).filter_by(attack_chain_id=chain.id).first() is not None
        assert db_session.query(RecommendationDB).filter_by(attack_chain_id=chain.id).first() is not None
        assert db_session.query(ReportDB).filter_by(attack_chain_id=chain.id).first() is not None

    def test_workflow_chain_not_found_fails_gracefully(self, db_session):
        """Test that missing chain stops workflow and returns failed status with error."""
        runner = ThreatWorkflowRunner(db=db_session)
        final_state = runner.run("NON_EXISTENT_CHAIN")

        assert final_state["status"] == "failed"
        assert len(final_state["errors"]) > 0
        assert any("not found" in err.lower() for err in final_state["errors"])
        # Subsequent nodes should have been skipped
        assert final_state["mitre_mappings"] is None
        assert final_state["risk_score"] is None

    def test_workflow_second_run_is_fast_due_to_caching(self, db_session):
        """Test that re-running workflow on an existing chain serves from cache without error."""
        _seed_chain(db_session, "AC_WF_CACHED", "PortScan,BruteForce")

        runner = ThreatWorkflowRunner(db=db_session)
        state1 = runner.run("AC_WF_CACHED")
        assert state1["status"] == "completed"

        # Second run
        state2 = runner.run("AC_WF_CACHED")
        assert state2["status"] == "completed"
        assert len(state2["errors"]) == 0


class TestWorkflowAPI:

    def test_api_run_workflow(self, client, db_session):
        """Test POST /api/v1/workflow/run/{chain_id} endpoint."""
        _seed_chain(db_session, "AC_API_1", "PortScan,CredentialDumping,Malware")

        response = client.post("/api/v1/workflow/run/AC_API_1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_status"] == "completed"
        assert data["chain_id"] == "AC_API_1"
        assert data["data"] is not None
        assert data["data"]["risk_score"]["score"] > 0
        assert len(data["data"]["mitre_mappings"]) > 0
        assert "executive_summary" in data["data"]["report"]

    def test_api_run_workflow_not_found(self, client):
        """Test POST /api/v1/workflow/run/{chain_id} with unknown chain returns 404."""
        response = client.post("/api/v1/workflow/run/UNKNOWN_CHAIN")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_api_get_workflow_status_pending_and_completed(self, client, db_session):
        """Test GET /api/v1/workflow/status/{chain_id} before and after workflow execution."""
        _seed_chain(db_session, "AC_STATUS_1", "PortScan,Malware")

        # Initial check: pending
        status_resp = client.get("/api/v1/workflow/status/AC_STATUS_1")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["chain_id"] == "AC_STATUS_1"
        assert status_data["status"] == "pending"
        assert status_data["has_attack_chain"] is True
        assert status_data["has_mitre_mapping"] is False

        # Run workflow
        client.post("/api/v1/workflow/run/AC_STATUS_1")

        # Check again: completed
        completed_resp = client.get("/api/v1/workflow/status/AC_STATUS_1")
        assert completed_resp.status_code == 200
        completed_data = completed_resp.json()
        assert completed_data["status"] == "completed"
        assert completed_data["has_mitre_mapping"] is True
        assert completed_data["has_risk_score"] is True
        assert completed_data["has_recommendations"] is True
        assert completed_data["has_report"] is True

    def test_api_get_workflow_status_not_found(self, client):
        """Test GET /api/v1/workflow/status/{chain_id} for unknown chain returns 404."""
        response = client.get("/api/v1/workflow/status/UNKNOWN_CHAIN")
        assert response.status_code == 404

    def test_api_run_all_workflows(self, client, db_session):
        """Test POST /api/v1/workflow/run-all batch execution."""
        _seed_chain(db_session, "AC_BATCH_1", "PortScan")
        _seed_chain(db_session, "AC_BATCH_2", "Malware")

        response = client.post("/api/v1/workflow/run-all")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_chains"] == 2
        assert data["completed_chains"] == 2
        assert data["failed_chains"] == 0
        assert len(data["results"]) == 2
