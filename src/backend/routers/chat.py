"""
FastAPI Router for the AI Analyst Chat System.
Provides endpoints for:
- POST /api/v1/chat: Ask question with RAG retrieval and analyst answer
- POST /api/v1/chat/new-session: Create fresh conversation session
- GET /api/v1/chat/history/{session_id}: Retrieve complete chat history
- POST /api/v1/chat/sync-knowledge: Sync threat data into Qdrant vector index
"""

import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from database.session import get_db
    from database.models import UserDB
    from routers.auth import get_current_user_obj
    from schemas.chat import (
        ChatRequest,
        ChatResponse,
        NewSessionResponse,
        ChatHistoryResponse,
    )
    from chat.analyst_chat import AnalystChatService
except ImportError:
    from backend.database.session import get_db
    from backend.database.models import UserDB
    from backend.routers.auth import get_current_user_obj
    from backend.schemas.chat import (
        ChatRequest,
        ChatResponse,
        NewSessionResponse,
        ChatHistoryResponse,
    )
    from backend.chat.analyst_chat import AnalystChatService

logger = logging.getLogger("threat_intelligence.router.chat")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["AI Analyst Chat"],
)

# Service singleton
_chat_service = AnalystChatService()


def get_chat_service() -> AnalystChatService:
    """Dependency provider for AnalystChatService."""
    return _chat_service


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Threat Intelligence AI Analyst",
    description="Submit a question to the AI Analyst. Retrieves context from Qdrant and returns a grounded response.",
)
def ask_analyst(
    payload: ChatRequest,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
    chat_service: AnalystChatService = Depends(get_chat_service),
):
    """
    Submits a query to the AI Analyst.
    Executes LangGraph workflow: Retrieve Node -> Answer Node -> Memory Node.
    """
    try:
        response = chat_service.ask(request=payload, db=db)
        return response
    except ValueError as e:
        logger.warning("Bad request in chat endpoint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Internal error processing chat query: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing the threat query: {str(e)}",
        )


@router.post(
    "/new-session",
    response_model=NewSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create New Chat Session",
    description="Generates a new unique session UUID for starting a fresh conversation.",
)
def create_session(
    chat_service: AnalystChatService = Depends(get_chat_service),
):
    """Generates a fresh session ID."""
    return chat_service.create_session()


@router.get(
    "/history/{session_id}",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Chat History",
    description="Returns the full conversation turn history for the specified session UUID.",
)
def get_session_history(
    session_id: str,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
    chat_service: AnalystChatService = Depends(get_chat_service),
):
    """Retrieves full conversation history."""
    try:
        return chat_service.get_history(session_id=session_id, db=db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Error retrieving chat history: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation history: {str(e)}",
        )


@router.post(
    "/sync-knowledge",
    status_code=status.HTTP_200_OK,
    summary="Synchronize Knowledge Base into Qdrant",
    description="Indexes existing Attack Chains, BLUF Reports, and Recommendations from PostgreSQL into Qdrant.",
)
def sync_knowledge(
    db: Session = Depends(get_db),
    chat_service: AnalystChatService = Depends(get_chat_service),
):
    """Populates Qdrant vector collection from existing database records."""
    try:
        indexed_count = chat_service.sync_knowledge_base(db=db)
        return {
            "status": "success",
            "message": f"Successfully synchronized {indexed_count} threat intelligence documents into Qdrant.",
            "indexed_count": indexed_count,
        }
    except Exception as e:
        logger.error("Knowledge base sync failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge synchronization failed: {str(e)}",
        )

