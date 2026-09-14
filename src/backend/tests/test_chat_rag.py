"""
Unit and integration tests for AI Analyst Chat System.
Tests Qdrant vector indexing, BAAI/bge-small-en-v1.5 embeddings, LangGraph workflow,
session persistence, grounded answer generation, and FastAPI endpoints.
"""

import json
from pathlib import Path
import sys
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import (
    Base,
    AttackChainDB,
    MitreMappingDB,
    RiskScoreDB,
    RecommendationDB,
    ReportDB,
    ChatHistoryDB,
    UserDB,
)
from database.session import get_db
from main import app
from schemas.chat import ChatRequest, ThreatDocSchema
from services.qdrant_service import QdrantService
from repositories.chat_repository import ChatRepository
from nodes.retrieve_node import retrieve_node
from nodes.answer_node import answer_node
from nodes.memory_node import memory_node
from graph.analyst_graph import build_analyst_graph
from chat.analyst_chat import AnalystChatService
from routers.chat import get_chat_service


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
        session.rollback()
        session.close()


@pytest.fixture
def test_qdrant():
    """Create an isolated in-memory Qdrant instance for test execution."""
    svc = QdrantService(in_memory=True, collection_name=f"threat_test_{uuid.uuid4().hex[:8]}")
    return svc


TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def populated_qdrant(test_qdrant):
    """Seed test Qdrant collection with representative threat intelligence documents."""
    docs = [
        {
            "chain_id": "AC001",
            "risk": "Critical",
            "summary": "Attack Chain AC001 has the highest risk score of 92 (Critical). The chain involved PortScan, BruteForce, CredentialDumping and Malware activity.",
            "mitre": ["T1110", "T1003"],
            "doc_type": "attack_chain",
            "user_id": TEST_USER_ID,
            "metadata": {"score": 92.0},
        },
        {
            "chain_id": "AC002",
            "risk": "High",
            "summary": "Attack Chain AC002 executed SQL Injection followed by Command Execution and Data Exfiltration.",
            "mitre": ["T1190", "T1059"],
            "doc_type": "attack_chain",
            "user_id": TEST_USER_ID,
            "metadata": {"score": 78.5},
        },
        {
            "chain_id": "AC003",
            "risk": "Medium",
            "summary": "Attack Chain AC003 demonstrated lateral movement using credential access via Kerberoasting.",
            "mitre": ["T1558", "T1003"],
            "doc_type": "attack_chain",
            "user_id": TEST_USER_ID,
            "metadata": {"score": 55.0},
        },
    ]
    test_qdrant.upsert_documents(docs)
    return test_qdrant


@pytest.fixture
def test_chat_service(populated_qdrant):
    """Create chat service backed by the populated test Qdrant."""
    return AnalystChatService(qdrant_service=populated_qdrant)


@pytest.fixture
def client(db_session, test_chat_service):
    """FastAPI TestClient with overridden DB, ChatService, and Auth dependencies."""
    from routers.auth import get_current_user_obj
    from database.models import UserDB

    dummy_user = UserDB(
        id=TEST_USER_ID,
        email="analyst@sentinelforge.mil",
        full_name="Lead SOC Analyst",
        hashed_password="hashed_password_mock",
    )
    db_session.add(dummy_user)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_chat_service] = lambda: test_chat_service
    app.dependency_overrides[get_current_user_obj] = lambda: dummy_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Unit Tests: Qdrant Service & Embeddings
# ---------------------------------------------------------------------------
class TestQdrantService:
    def test_embedding_computation_and_cache(self, test_qdrant):
        query = "What is the highest risk attack?"
        vec1 = test_qdrant.get_embedding(query)
        assert len(vec1) == 384
        # Second retrieval should hit cache
        vec2 = test_qdrant.get_embedding(query)
        assert vec1 == vec2

    def test_document_upsert_and_similarity_search(self, test_qdrant):
        doc = {
            "chain_id": "AC999",
            "risk": "Critical",
            "summary": "Ransomware payload execution targeting healthcare servers.",
            "mitre": ["T1486", "T1489"],
        }
        point_id = test_qdrant.upsert_document(doc)
        assert point_id is not None

        # Search
        results = test_qdrant.search(query="ransomware encryption", top_k=2)
        assert len(results) >= 1
        assert results[0].chain_id == "AC999"
        assert "T1486" in results[0].mitre

    def test_filtered_search_by_risk(self, populated_qdrant):
        results = populated_qdrant.search(query="attack", top_k=5, filter_risk="Critical")
        assert len(results) >= 1
        for res in results:
            assert res.risk == "Critical"

    def test_filtered_search_by_chain_id(self, populated_qdrant):
        results = populated_qdrant.search(query="attack", top_k=5, filter_chain_id="AC002")
        assert len(results) == 1
        assert results[0].chain_id == "AC002"

    def test_filtered_search_by_mitre(self, populated_qdrant):
        results = populated_qdrant.search(query="attack", top_k=5, filter_mitre="T1190")
        assert len(results) >= 1
        assert "T1190" in results[0].mitre

    def test_filtered_search_by_user_id(self, test_qdrant):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        doc_a = {
            "chain_id": "AC_A",
            "risk": "Critical",
            "summary": "User A confidential threat intelligence on finance database 10.1.1.5.",
            "mitre": ["T1003"],
            "user_id": user_a,
        }
        doc_b = {
            "chain_id": "AC_B",
            "risk": "Low",
            "summary": "User B routine port scan log on 192.168.1.1.",
            "mitre": ["T1046"],
            "user_id": user_b,
        }
        test_qdrant.upsert_documents([doc_a, doc_b])

        # Search as User A
        results_a = test_qdrant.search(query="threat database", filter_user_id=user_a)
        assert len(results_a) == 1
        assert results_a[0].chain_id == "AC_A"
        assert str(results_a[0].user_id) == user_a

        # Search as User B (even for query that matches User A)
        results_b = test_qdrant.search(query="threat database", filter_user_id=user_b)
        # All returned results must belong to User B only, never User A
        for r in results_b:
            assert str(r.user_id) == user_b
            assert r.chain_id != "AC_A"

        # Search as User A (must never return User B's doc)
        results_a_port = test_qdrant.search(query="port scan", filter_user_id=user_a)
        for r in results_a_port:
            assert str(r.user_id) == user_a
            assert r.chain_id != "AC_B"


# ---------------------------------------------------------------------------
# Unit Tests: Chat Repository
# ---------------------------------------------------------------------------
class TestChatRepository:
    def test_save_and_retrieve_history(self, db_session):
        repo = ChatRepository(db_session)
        session_id = uuid.uuid4()

        repo.save_message(session_id=session_id, role="user", message="Show me critical attacks")
        repo.save_message(session_id=session_id, role="assistant", message="Found AC001 with Critical risk.")

        history = repo.get_history(session_id=session_id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].message == "Show me critical attacks"
        assert history[1].role == "assistant"
        assert history[1].message == "Found AC001 with Critical risk."

    def test_delete_history(self, db_session):
        repo = ChatRepository(db_session)
        session_id = uuid.uuid4()
        repo.save_message(session_id=session_id, role="user", message="Test message")
        assert repo.session_exists(session_id) is True

        deleted_count = repo.delete_history(session_id=session_id)
        assert deleted_count == 1
        assert repo.session_exists(session_id) is False


# ---------------------------------------------------------------------------
# Unit Tests: LangGraph Nodes
# ---------------------------------------------------------------------------
class TestLangGraphNodes:
    def test_retrieve_node(self, populated_qdrant):
        state = {
            "question": "Which attack involved credential theft?",
            "top_k": 3,
            "_qdrant_service": populated_qdrant,
        }
        out_state = retrieve_node(state)
        docs = out_state.get("retrieved_documents", [])
        assert len(docs) > 0
        chain_ids = [d["chain_id"] for d in docs]
        assert "AC001" in chain_ids or "AC003" in chain_ids

    def test_answer_node_with_grounded_fallback(self):
        retrieved_docs = [
            {
                "chain_id": "AC001",
                "risk": "Critical",
                "summary": "PortScan and BruteForce activity targeting SSH port.",
                "mitre": ["T1110", "T1003"],
            }
        ]
        state = {
            "question": "What is the highest risk attack?",
            "retrieved_documents": retrieved_docs,
            "chat_history": [],
        }
        out_state = answer_node(state)
        ans = out_state.get("answer", "")
        assert "AC001" in ans
        assert "Critical" in ans

    def test_answer_node_empty_docs(self):
        state = {
            "question": "What is unknown incident 9999?",
            "retrieved_documents": [],
            "chat_history": [],
        }
        out_state = answer_node(state)
        assert "No matching threat intelligence records" in out_state.get("answer", "")

    def test_memory_node(self, db_session):
        session_id = str(uuid.uuid4())
        state = {
            "session_id": session_id,
            "question": "Identify MITRE T1003",
            "answer": "Attack chain AC001 maps to T1003.",
            "chat_history": [],
            "_db": db_session,
        }
        out_state = memory_node(state)
        history = out_state.get("chat_history", [])
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

        # Verify persisted in database
        repo = ChatRepository(db_session)
        db_records = repo.get_history(uuid.UUID(session_id))
        assert len(db_records) == 2


# ---------------------------------------------------------------------------
# Integration Tests: End-to-End AnalystChatService
# ---------------------------------------------------------------------------
class TestAnalystChatService:
    def test_create_session(self, test_chat_service):
        resp = test_chat_service.create_session()
        assert resp.session_id is not None
        uuid.UUID(resp.session_id)  # Should not raise

    def test_ask_highest_risk(self, test_chat_service, db_session):
        sess_resp = test_chat_service.create_session()
        req = ChatRequest(
            session_id=sess_resp.session_id,
            question="What is the highest risk attack?",
        )
        response = test_chat_service.ask(request=req, db=db_session)
        assert response.answer is not None
        assert "AC001" in response.answer or "Critical" in response.answer
        assert len(response.retrieved_documents) > 0

    def test_ask_credential_theft(self, test_chat_service, db_session):
        sess_resp = test_chat_service.create_session()
        req = ChatRequest(
            session_id=sess_resp.session_id,
            question="Which attacks involved credential theft?",
        )
        response = test_chat_service.ask(request=req, db=db_session)
        assert response.answer is not None
        assert "credential" in response.answer.lower() or "AC001" in response.answer

    def test_ask_with_filter(self, test_chat_service, db_session):
        sess_resp = test_chat_service.create_session()
        req = ChatRequest(
            session_id=sess_resp.session_id,
            question="Tell me about this attack",
            filter_chain_id="AC002",
        )
        response = test_chat_service.ask(request=req, db=db_session)
        assert response.answer is not None
        assert any(d.chain_id == "AC002" for d in response.retrieved_documents)


# ---------------------------------------------------------------------------
# API Integration Tests: FastAPI Endpoints
# ---------------------------------------------------------------------------
class TestChatEndpoints:
    def test_new_session_endpoint(self, client):
        resp = client.post("/api/v1/chat/new-session")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        uuid.UUID(data["session_id"])

    def test_chat_endpoint_valid_query(self, client):
        # Create session
        sess_res = client.post("/api/v1/chat/new-session").json()
        session_id = sess_res["session_id"]

        # Ask question
        payload = {
            "session_id": session_id,
            "question": "What is the highest risk attack?",
        }
        resp = client.post("/api/v1/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        assert data["session_id"] == session_id
        assert len(data["retrieved_documents"]) > 0

    def test_chat_history_endpoint(self, client):
        sess_res = client.post("/api/v1/chat/new-session").json()
        session_id = sess_res["session_id"]

        # Send turn 1
        client.post("/api/v1/chat", json={"session_id": session_id, "question": "Question 1"})
        # Send turn 2
        client.post("/api/v1/chat", json={"session_id": session_id, "question": "Question 2"})

        # Get history
        hist_resp = client.get(f"/api/v1/chat/history/{session_id}")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert hist_data["total_messages"] == 4  # 2 user + 2 assistant
        assert len(hist_data["history"]) == 4

    def test_chat_invalid_session_id(self, client):
        payload = {
            "session_id": "not-a-valid-uuid",
            "question": "Hello?",
        }
        resp = client.post("/api/v1/chat", json=payload)
        assert resp.status_code == 400

    def test_sync_knowledge_endpoint(self, client, db_session):
        # Seed an attack chain in DB
        user = db_session.query(UserDB).first()
        chain = AttackChainDB(
            id=uuid.uuid4(),
            user_id=user.id if user else None,
            chain_id="AC_SYNC_01",
            source_ip="192.168.1.100",
            destination_ips="10.0.0.5",
            events="PortScan, BruteForce",
            alert_count=2,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        db_session.add(chain)
        db_session.commit()

        resp = client.post("/api/v1/chat/sync-knowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["indexed_count"] >= 1
