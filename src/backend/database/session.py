"""
Database session factory and FastAPI dependency for the Threat Intelligence backend.

Reads DATABASE_URL from the environment. When no URL is set (e.g. during unit tests
that import main.py but don't need a live database), the engine creation is deferred
so the import itself never crashes.
"""

import logging
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger("database.session")

# Automatically load .env from project root or backend directory
_root_env = Path(__file__).resolve().parent.parent.parent / ".env"
_backend_env = Path(__file__).resolve().parent.parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env)
elif _backend_env.exists():
    load_dotenv(_backend_env)
else:
    load_dotenv()

# Engine and session factory are created lazily so that importing this module
# without DATABASE_URL set (e.g. during tests) does not crash.
_engine = None
_SessionLocal = None


def _get_engine():
    """Lazily create the SQLAlchemy engine on first use."""
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL", "").strip('"\'')
        if not db_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "Provide a valid PostgreSQL connection string in .env."
            )
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        _engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            future=True,
        )
        logger.info("Database engine created successfully")
    return _engine


def _get_session_factory():
    """Lazily create the session factory on first use."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            future=True,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session per request.

    Usage in FastAPI routes::

        def endpoint(..., db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = _get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
