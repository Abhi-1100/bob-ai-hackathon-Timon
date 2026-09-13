"""
Unit tests for the Alert Correlation Engine.
Uses an in-memory SQLite database to avoid requiring a live PostgreSQL instance.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import Base, Upload, Alert as AlertDB, AttackChainDB, AttackChainEventDB
from services.alert_correlation import AlertCorrelationEngine, CorrelationError


# ---------------------------------------------------------------------------
# Fixtures – in-memory SQLite session
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite DB with all tables for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # SQLite does not natively support UUID – render as VARCHAR
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


def _seed_upload(session) -> uuid.UUID:
    """Create a dummy upload record and return its UUID."""
    upload = Upload(
        id=uuid.uuid4(),
        file_name="test_alerts.csv",
        file_path="uploads/test_alerts.csv",
    )
    session.add(upload)
    session.commit()
    return upload.id


def _seed_alerts(session, upload_id: uuid.UUID, alerts_data: list) -> None:
    """Insert alert rows from a list of dicts."""
    for ad in alerts_data:
        alert = AlertDB(
            id=uuid.uuid4(),
            upload_id=upload_id,
            timestamp=ad["timestamp"],
            src_ip=ad["src_ip"],
            dst_ip=ad["dst_ip"],
            event=ad["event"],
            severity=ad["severity"],
        )
        session.add(alert)
    session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestCorrelationEngine:

    def test_no_alerts_raises_error(self, db_session):
        """Engine should raise CorrelationError if the database is empty."""
        engine = AlertCorrelationEngine(db=db_session)
        with pytest.raises(CorrelationError, match="No alerts found"):
            engine.correlate(persist=False)

    def test_single_source_ip_single_chain(self, db_session):
        """All alerts from one source IP within the time window form one chain."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
            {"timestamp": base + timedelta(minutes=2), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "BruteForce", "severity": "High"},
            {"timestamp": base + timedelta(minutes=5), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "Malware", "severity": "Critical"},
        ])

        engine = AlertCorrelationEngine(db=db_session)
        result = engine.correlate(persist=False)

        assert result.chains_created == 1
        assert result.alerts_processed == 3

        chain = result.chains[0]
        assert chain.source_ip == "10.0.0.1"
        assert chain.alert_count == 3
        assert "PortScan" in chain.events
        assert "BruteForce" in chain.events
        assert "Malware" in chain.events

    def test_time_window_splits_chains(self, db_session):
        """Alerts separated by more than the time window form separate chains."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
            {"timestamp": base + timedelta(hours=4), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "BruteForce", "severity": "High"},
        ])

        engine = AlertCorrelationEngine(db=db_session, time_window_minutes=30)
        result = engine.correlate(persist=False)

        assert result.chains_created == 2
        assert result.alerts_processed == 2

    def test_different_source_ips_separate_chains(self, db_session):
        """Alerts from different source IPs form separate chains even within time window."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
            {"timestamp": base + timedelta(minutes=1), "src_ip": "10.0.0.2", "dst_ip": "10.0.0.5", "event": "BruteForce", "severity": "High"},
        ])

        engine = AlertCorrelationEngine(db=db_session)
        result = engine.correlate(persist=False)

        assert result.chains_created == 2
        source_ips = {c.source_ip for c in result.chains}
        assert source_ips == {"10.0.0.1", "10.0.0.2"}

    def test_severity_summary(self, db_session):
        """Chains should contain a correct severity breakdown."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
            {"timestamp": base + timedelta(minutes=1), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
            {"timestamp": base + timedelta(minutes=2), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "BruteForce", "severity": "High"},
        ])

        engine = AlertCorrelationEngine(db=db_session)
        result = engine.correlate(persist=False)

        chain = result.chains[0]
        assert chain.severity_summary.get("Medium") == 2
        assert chain.severity_summary.get("High") == 1

    def test_destination_ips_collected(self, db_session):
        """Chain should list all unique destination IPs."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
            {"timestamp": base + timedelta(minutes=1), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.6", "event": "BruteForce", "severity": "High"},
            {"timestamp": base + timedelta(minutes=2), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "Malware", "severity": "Critical"},
        ])

        engine = AlertCorrelationEngine(db=db_session)
        result = engine.correlate(persist=False)

        chain = result.chains[0]
        assert set(chain.destination_ips) == {"10.0.0.5", "10.0.0.6"}

    def test_chain_id_format(self, db_session):
        """Chain IDs should follow AC001, AC002, AC003... pattern."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Low"},
            {"timestamp": base + timedelta(hours=5), "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "BruteForce", "severity": "High"},
            {"timestamp": base, "src_ip": "10.0.0.2", "dst_ip": "10.0.0.5", "event": "Malware", "severity": "Critical"},
        ])

        engine = AlertCorrelationEngine(db=db_session, time_window_minutes=30)
        result = engine.correlate(persist=False)

        chain_ids = sorted([c.chain_id for c in result.chains])
        # We should have 3 chains (2 from IP .1 split by time, 1 from IP .2)
        assert len(chain_ids) == 3
        for cid in chain_ids:
            assert cid.startswith("AC")

    def test_execution_time_reported(self, db_session):
        """CorrelationResult should include a non-negative execution time."""
        upload_id = _seed_upload(db_session)
        base = datetime(2026, 9, 13, 10, 0, 0)
        _seed_alerts(db_session, upload_id, [
            {"timestamp": base, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"},
        ])

        engine = AlertCorrelationEngine(db=db_session)
        result = engine.correlate(persist=False)

        assert result.execution_time_ms >= 0
