"""
Repository for persisting and querying chat history in PostgreSQL.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

try:
    from database.models import ChatHistoryDB
except ImportError:
    from backend.database.models import ChatHistoryDB


class ChatRepository:
    """Repository handling CRUD operations for chat session turns."""

    def __init__(self, db: Session):
        self.db = db

    def save_message(self, session_id: uuid.UUID, role: str, message: str) -> ChatHistoryDB:
        """Persist a user or assistant message to database."""
        chat_entry = ChatHistoryDB(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            message=message,
        )
        self.db.add(chat_entry)
        self.db.commit()
        self.db.refresh(chat_entry)
        return chat_entry

    def get_history(self, session_id: uuid.UUID, limit: int = 50) -> List[ChatHistoryDB]:
        """Retrieve conversation turns for a session in chronological order."""
        stmt = (
            select(ChatHistoryDB)
            .where(ChatHistoryDB.session_id == session_id)
            .order_by(ChatHistoryDB.created_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def delete_history(self, session_id: uuid.UUID) -> int:
        """Delete all messages associated with a session."""
        stmt = delete(ChatHistoryDB).where(ChatHistoryDB.session_id == session_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def session_exists(self, session_id: uuid.UUID) -> bool:
        """Check if any message exists for this session."""
        stmt = (
            select(ChatHistoryDB.id)
            .where(ChatHistoryDB.session_id == session_id)
            .limit(1)
        )
        return self.db.scalar(stmt) is not None
