"""
Memory Node for AI Analyst Chat System.
Persists user and assistant messages into PostgreSQL chat_history table
and updates state conversation history.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
import uuid

from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

try:
    from repositories.chat_repository import ChatRepository
    from database.session import _get_session_factory
except ImportError:
    from backend.repositories.chat_repository import ChatRepository
    from backend.database.session import _get_session_factory

logger = logging.getLogger("threat_intelligence.nodes.memory")


def memory_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Saves user question and generated analyst answer to the PostgreSQL chat_history table.
    Updates chat_history in state to reflect the latest messages.
    """
    session_id_raw = state.get("session_id")
    question = state.get("question", "").strip()
    answer = state.get("answer", "").strip()

    state["timestamp"] = datetime.now(timezone.utc).isoformat()

    if not session_id_raw:
        logger.warning("No session_id present in state. Skipping persistent chat history storage.")
        return state

    try:
        if isinstance(session_id_raw, uuid.UUID):
            session_uuid = session_id_raw
        else:
            session_uuid = uuid.UUID(str(session_id_raw))
    except Exception as e:
        logger.error("Invalid session_id format '%s': %s", session_id_raw, str(e))
        return state

    # Resolve database session
    db: Optional[Session] = state.get("_db")
    if not db and config:
        db = config.get("configurable", {}).get("db")

    close_db_after = False
    if not db:
        try:
            db = _get_session_factory()()
            close_db_after = True
        except Exception as exc:
            logger.error("Could not obtain database session for chat history persistence: %s", exc)
            return state

    try:
        repo = ChatRepository(db)
        if question:
            repo.save_message(session_id=session_uuid, role="user", message=question)
        if answer:
            repo.save_message(session_id=session_uuid, role="assistant", message=answer)

        # Update state chat_history
        history = list(state.get("chat_history", []))
        if question:
            history.append({"role": "user", "message": question, "timestamp": state["timestamp"]})
        if answer:
            history.append({"role": "assistant", "message": answer, "timestamp": state["timestamp"]})
        state["chat_history"] = history

        logger.info("History stored for session: %s", str(session_uuid))
    except Exception as exc:
        logger.error("Failed to store chat history: %s", str(exc), exc_info=True)
    finally:
        if close_db_after and db:
            db.close()

    return state
