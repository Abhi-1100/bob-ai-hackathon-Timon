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


def _get_database_url() -> str:
    """Return configured DATABASE_URL or default fallback."""
    db_url = os.getenv("DATABASE_URL", "").strip('"\'')
    if not db_url or "username:password@host" in db_url or "host:5432" in db_url:
        return "sqlite:///./threat_intel.db"
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return db_url


def _get_engine():
    """Lazily create the SQLAlchemy engine on first use with automatic fallback."""
    global _engine
    if _engine is None:
        db_url = _get_database_url()
        if db_url.startswith("sqlite"):
            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                future=True,
            )
            logger.info(f"Local SQLite database engine initialized successfully ({db_url})")
        else:
            try:
                engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    pool_size=15,
                    max_overflow=25,
                    pool_timeout=10,
                    connect_args={
                        "connect_timeout": 5,
                    },
                    future=True,
                )
                # Test connection to verify PostgreSQL is reachable
                with engine.connect() as conn:
                    pass
                _engine = engine
                logger.info("High-performance PostgreSQL database engine created successfully")
            except Exception as exc:
                logger.warning(
                    f"PostgreSQL connection failed ({exc}). Falling back to local SQLite database."
                )
                fallback_url = "sqlite:///./threat_intel.db"
                _engine = create_engine(
                    fallback_url,
                    connect_args={"check_same_thread": False},
                    future=True,
                )
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


def SessionLocal() -> Session:
    """Convenience helper to obtain a new SQLAlchemy session for background tasks."""
    factory = _get_session_factory()
    return factory()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session per request.

    Usage in FastAPI routes::

        def endpoint(..., db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
