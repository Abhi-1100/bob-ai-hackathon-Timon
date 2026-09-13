"""
Production-ready AI Analyst Chat Service.
Orchestrates Qdrant document retrieval, LangGraph workflow execution,
Groq Llama 3.3 70B response synthesis, and PostgreSQL conversation memory.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

try:
    from graph.analyst_graph import analyst_graph_app, ChatState
    from repositories.chat_repository import ChatRepository
    from schemas.chat import (
        ChatRequest,
        ChatResponse,
        NewSessionResponse,
        ChatMessage,
        ChatHistoryResponse,
        ThreatDocSchema,
    )
    from services.qdrant_service import QdrantService
except ImportError:
    from backend.graph.analyst_graph import analyst_graph_app, ChatState
    from backend.repositories.chat_repository import ChatRepository
    from backend.schemas.chat import (
        ChatRequest,
        ChatResponse,
        NewSessionResponse,
        ChatMessage,
        ChatHistoryResponse,
        ThreatDocSchema,
    )
    from backend.services.qdrant_service import QdrantService

logger = logging.getLogger("threat_intelligence.chat.service")


class AnalystChatService:
    """
    Coordinator service providing high-level chat query execution,
    session management, and chat history retrieval.
    """

    def __init__(self, qdrant_service: Optional[QdrantService] = None):
        self.qdrant_service = qdrant_service or QdrantService.get_instance()

    def create_session(self) -> NewSessionResponse:
        """Create a new chat session UUID."""
        new_id = str(uuid.uuid4())
        logger.info("Generated new analyst chat session: %s", new_id)
        return NewSessionResponse(session_id=new_id)

    def ask(self, request: ChatRequest, db: Session) -> ChatResponse:
        """
        Process a user question through the LangGraph RAG workflow:
        1. Fetch conversation history from PostgreSQL
        2. Execute LangGraph workflow (Retrieve -> Answer -> Memory)
        3. Return grounded response with explainability metadata
        """
        start_time = time.time()
        logger.info("Incoming analyst chat question for session %s: '%s'", request.session_id, request.question)

        # Validate session UUID format
        try:
            session_uuid = uuid.UUID(request.session_id)
        except ValueError:
            raise ValueError(f"Invalid session_id format: '{request.session_id}'. Must be a valid UUID.")

        # 1. Fetch recent conversation history
        chat_repo = ChatRepository(db)
        history_records = chat_repo.get_history(session_id=session_uuid, limit=10)
        formatted_history = [
            {
                "role": record.role,
                "message": record.message,
                "timestamp": record.created_at.isoformat() if record.created_at else "",
            }
            for record in history_records
        ]

        # 2. Build initial LangGraph ChatState
        initial_state: ChatState = {
            "question": request.question,
            "retrieved_documents": [],
            "answer": "",
            "chat_history": formatted_history,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": str(session_uuid),
            "filter_chain_id": request.filter_chain_id,
            "filter_risk": request.filter_risk,
            "filter_mitre": request.filter_mitre,
            "top_k": request.top_k,
            "_db": db,
            "_qdrant_service": self.qdrant_service,
        }

        # 3. Invoke compiled LangGraph workflow
        final_state = analyst_graph_app.invoke(initial_state)

        # 4. Package response
        raw_docs = final_state.get("retrieved_documents", [])
        parsed_docs: List[ThreatDocSchema] = []
        for d in raw_docs:
            if isinstance(d, ThreatDocSchema):
                parsed_docs.append(d)
            elif isinstance(d, dict):
                parsed_docs.append(ThreatDocSchema(**d))

        elapsed_time = round(time.time() - start_time, 4)
        logger.info("Analyst chat response generated for session %s in %.3fs", request.session_id, elapsed_time)

        return ChatResponse(
            answer=final_state.get("answer", "No response could be generated."),
            session_id=str(session_uuid),
            retrieved_documents=parsed_docs,
            execution_time_seconds=elapsed_time,
        )

    def get_history(self, session_id: str, db: Session) -> ChatHistoryResponse:
        """Fetch chronological message history for a given session."""
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise ValueError(f"Invalid session_id format: '{session_id}'. Must be a valid UUID.")

        chat_repo = ChatRepository(db)
        records = chat_repo.get_history(session_id=session_uuid, limit=100)
        messages = [
            ChatMessage(
                id=r.id,
                session_id=r.session_id,
                role=r.role,
                message=r.message,
                created_at=r.created_at,
            )
            for r in records
        ]
        return ChatHistoryResponse(
            session_id=str(session_uuid),
            total_messages=len(messages),
            history=messages,
        )

    def sync_knowledge_base(self, db: Session) -> int:
        """Harvest current database attack chains and reports into Qdrant."""
        logger.info("Syncing relational threat intelligence data into Qdrant collection")
        count = self.qdrant_service.sync_from_database(db)
        logger.info("Sync complete. %d intelligence documents indexed.", count)
        return count
