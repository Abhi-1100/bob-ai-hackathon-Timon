"""
End-to-End System Workflow Integration Test.
Tests the complete lifecycle from CSV upload to AI Analyst Chat:
1. CSV Upload & Database Ingestion (Uploads & Alerts tables)
2. Alert Correlation Engine (Attack Chains)
3. LangGraph Workflow Orchestration (MITRE -> Risk -> Recs -> BLUF Report -> Store)
4. Knowledge Base Synchronization (PostgreSQL -> Qdrant vector index)
5. AI Analyst Chat RAG System (Multi-turn conversational grounded query & memory)
"""

import io
from pathlib import Path
import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import Base
from database.session import get_db
from main import app
from services.qdrant_service import QdrantService
from chat.analyst_chat import AnalystChatService
from routers.chat import get_chat_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite DB with all tables for end-to-end testing."""
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
        session.rollback()
        session.close()


@pytest.fixture
def isolated_qdrant():
    """Create an isolated in-memory Qdrant instance for the end-to-end test."""
    return QdrantService(in_memory=True, collection_name=f"threat_e2e_{uuid.uuid4().hex[:8]}")


@pytest.fixture
def e2e_chat_service(isolated_qdrant):
    """Create chat service backed by the isolated Qdrant vector store."""
    return AnalystChatService(qdrant_service=isolated_qdrant)


@pytest.fixture
def client(db_session, e2e_chat_service):
    """FastAPI TestClient with overridden DB and ChatService dependencies."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_chat_service] = lambda: e2e_chat_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# End-to-End Workflow Test
# ---------------------------------------------------------------------------
def test_full_threat_intelligence_pipeline(client, db_session):
    """
    Validates complete 10-step lifecycle of the Threat Intelligence Assistant:
    CSV Upload -> Parsing -> Storage -> Correlation -> MITRE -> Risk -> Recs -> BLUF -> Qdrant -> Chat.
    """

    # =========================================================================
    # STEP 1: CSV Upload & Ingestion into Database
    # =========================================================================
    sample_csv = (
        "timestamp,src_ip,dst_ip,event,severity\n"
        "2026-09-13 10:00:00,192.168.1.50,10.0.0.10,PortScan,Medium\n"
        "2026-09-13 10:05:00,192.168.1.50,10.0.0.10,BruteForce,High\n"
        "2026-09-13 10:10:00,192.168.1.50,10.0.0.10,CredentialDumping,Critical\n"
        "2026-09-13 10:15:00,192.168.1.50,10.0.0.10,Malware,High\n"
        "2026-09-13 10:02:00,192.168.2.88,10.0.0.25,SqlInjection,High\n"
        "2026-09-13 10:08:00,192.168.2.88,10.0.0.25,CommandExecution,Critical\n"
    )

    files = {"file": ("enterprise_alerts.csv", io.BytesIO(sample_csv.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/upload/ingest", files=files)
    assert upload_res.status_code == 201, f"Upload/ingest failed: {upload_res.text}"
    upload_data = upload_res.json()
    assert upload_data["success"] is True
    assert upload_data["alerts_ingested"] == 6
    assert "upload_id" in upload_data

    # =========================================================================
    # STEP 2: Alert Correlation Engine
    # =========================================================================
    correlate_res = client.get("/api/v1/chains/generate")
    assert correlate_res.status_code == 200, f"Correlation failed: {correlate_res.text}"
    correlate_data = correlate_res.json()
    assert correlate_data["chains_created"] >= 2
    chains = correlate_data["chains"]
    chain_ids = [c["chain_id"] for c in chains]
    assert len(chain_ids) >= 2

    lead_chain_id = chain_ids[0]

    # =========================================================================
    # STEP 3: LangGraph Threat Intelligence Workflow (End-to-End Orchestration)
    # Orchestrates: LoadChain -> MITRE -> Risk -> Recommendations -> BLUF Report -> StoreResults
    # =========================================================================
    wf_batch_res = client.post("/api/v1/workflow/run-all")
    assert wf_batch_res.status_code == 200, f"Workflow run-all failed: {wf_batch_res.text}"
    batch_data = wf_batch_res.json()
    assert batch_data["total_chains"] >= 2
    assert batch_data["completed_chains"] >= 2
    assert batch_data["failed_chains"] == 0

    # Verify artifacts for lead chain
    status_res = client.get(f"/api/v1/workflow/status/{lead_chain_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "completed"
    assert status_data["has_mitre_mapping"] is True
    assert status_data["has_risk_score"] is True
    assert status_data["has_recommendations"] is True
    assert status_data["has_report"] is True

    # =========================================================================
    # STEP 4: Synchronize Threat Intelligence into Qdrant Vector Store
    # =========================================================================
    sync_res = client.post("/api/v1/chat/sync-knowledge")
    assert sync_res.status_code == 200, f"Knowledge sync failed: {sync_res.text}"
    sync_data = sync_res.json()
    assert sync_data["status"] == "success"
    assert sync_data["indexed_count"] >= 2  # Chains + reports + recommendations indexed

    # =========================================================================
    # STEP 5: Start AI Analyst Chat Session
    # =========================================================================
    session_res = client.post("/api/v1/chat/new-session")
    assert session_res.status_code == 200
    session_data = session_res.json()
    session_id = session_data["session_id"]
    assert session_id is not None

    # =========================================================================
    # STEP 6: AI Analyst Chat Query 1 (Highest Risk Attack)
    # =========================================================================
    chat_q1 = {
        "session_id": session_id,
        "question": "What is the highest risk attack?",
        "top_k": 5,
    }
    chat_res1 = client.post("/api/v1/chat", json=chat_q1)
    assert chat_res1.status_code == 200, f"Chat Q1 failed: {chat_res1.text}"
    chat_data1 = chat_res1.json()
    assert "answer" in chat_data1
    assert len(chat_data1["answer"]) > 0
    assert len(chat_data1["retrieved_documents"]) > 0
    # Answer should be grounded in the correlated chains
    assert "AC" in chat_data1["answer"] or "risk" in chat_data1["answer"].lower()

    # =========================================================================
    # STEP 7: AI Analyst Chat Query 2 (Credential Theft Inquiry)
    # =========================================================================
    chat_q2 = {
        "session_id": session_id,
        "question": "Which attacks involved credential theft?",
        "top_k": 5,
    }
    chat_res2 = client.post("/api/v1/chat", json=chat_q2)
    assert chat_res2.status_code == 200, f"Chat Q2 failed: {chat_res2.text}"
    chat_data2 = chat_res2.json()
    assert "answer" in chat_data2
    assert (
        "credential" in chat_data2["answer"].lower()
        or "t1003" in chat_data2["answer"].lower()
        or "ac" in chat_data2["answer"].lower()
    )

    # =========================================================================
    # STEP 8: Verify Multi-turn Chat History in PostgreSQL
    # =========================================================================
    history_res = client.get(f"/api/v1/chat/history/{session_id}")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["session_id"] == session_id
    assert history_data["total_messages"] == 4  # 2 user queries + 2 assistant answers
    messages = history_data["history"]
    assert messages[0]["role"] == "user"
    assert "highest risk" in messages[0]["message"].lower()
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert "credential" in messages[2]["message"].lower()
    assert messages[3]["role"] == "assistant"
