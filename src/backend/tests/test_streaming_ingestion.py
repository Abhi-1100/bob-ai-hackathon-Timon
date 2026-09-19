"""Phase 1 tests for normalization and idempotent push ingestion."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Alert as AlertDB, AttackChainEventDB, Base, Upload, UserDB
from services.alert_correlation import AlertCorrelationEngine
from services.ingestion import ingest_raw_events
from services.normalizer import AlertNormalizer, NormalizationError


def test_source_field_maps_and_nested_paths():
    wazuh = AlertNormalizer("wazuh").normalize({
        "timestamp": "2026-09-19T10:00:00Z", "data": {"srcip": "10.0.0.1", "dstip": "10.0.0.5"},
        "rule": {"description": "brute force", "level": 12},
    })
    assert wazuh.event == "BruteForce"
    assert wazuh.severity == "High"
    assert wazuh.timestamp.tzinfo == timezone.utc

    suricata = AlertNormalizer("suricata").normalize({
        "timestamp": "2026-09-19T10:00:00+00:00", "src_ip": "192.0.2.1", "dest_ip": "192.0.2.2",
        "alert": {"signature": "Port Scan", "severity": 1},
    })
    assert suricata.event == "PortScan"
    assert suricata.severity == "Low"


def test_normalizer_rejects_invalid_ip_and_timestamp():
    normalizer = AlertNormalizer()
    raw = {"timestamp": "not-a-date", "src_ip": "999.1.1.1", "dst_ip": "10.0.0.1", "event": "x", "severity": "Low"}
    try:
        normalizer.normalize(raw)
    except NormalizationError as exc:
        assert "timestamp" in str(exc)
    else:
        raise AssertionError("invalid event was accepted")


def test_duplicate_events_are_idempotent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = UserDB(id=uuid.uuid4(), email="stream-test@example.com", hashed_password="x", full_name="Stream Test")
    session.add(user)
    session.commit()
    event = {"timestamp": "2026-09-19T10:00:00Z", "src_ip": "10.0.0.1", "dst_ip": "10.0.0.5", "event": "PortScan", "severity": "Medium"}
    assert ingest_raw_events(session, user.id, "generic", [event, event]) == {"received": 2, "accepted": 1, "rejected": 0}
    assert session.query(AlertDB).count() == 1
    session.close()


def test_incremental_correlation_joins_and_splits_by_timestamp():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = UserDB(id=uuid.uuid4(), email="corr-test@example.com", hashed_password="x", full_name="Corr Test")
    upload = Upload(id=uuid.uuid4(), file_name="stream", file_path="stream")
    session.add_all([user, upload])
    session.commit()

    def alert(minutes: int, event: str) -> AlertDB:
        row = AlertDB(id=uuid.uuid4(), user_id=user.id, upload_id=upload.id,
                      timestamp=datetime(2026, 9, 19, 10, minutes, tzinfo=timezone.utc),
                      src_ip="10.0.0.1", dst_ip="10.0.0.2", event=event, severity="Medium")
        session.add(row)
        session.commit()
        return row

    correlation = AlertCorrelationEngine(session)
    first = correlation.add_alert(alert(0, "PortScan"), user.id)
    same = correlation.add_alert(alert(10, "BruteForce"), user.id)
    split = correlation.add_alert(alert(41, "DataExfiltration"), user.id)
    assert first.chain_id == same.chain_id
    assert split.chain_id != same.chain_id
    assert session.query(AttackChainEventDB).count() == 3
    session.close()
