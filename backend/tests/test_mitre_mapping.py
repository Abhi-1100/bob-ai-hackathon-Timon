"""
Unit tests for the MITRE ATT&CK Mapping Service.
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

from database.models import Base, Upload, Alert as AlertDB, AttackChainDB, MitreMappingDB
from services.mitre_mapping import MitreMappingService, MitreMappingError, MITRE_KNOWLEDGE_BASE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite DB with all tables for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)

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


def _create_chain(session, chain_id: str, events: str, source_ip: str = "10.0.0.1") -> AttackChainDB:
    """Helper to seed an attack chain record."""
    chain = AttackChainDB(
        id=uuid.uuid4(),
        chain_id=chain_id,
        source_ip=source_ip,
        destination_ips="10.0.0.5",
        events=events,
        alert_count=len(events.split(",")),
        start_time=datetime(2026, 9, 13, 10, 0, 0),
        end_time=datetime(2026, 9, 13, 10, 30, 0),
    )
    session.add(chain)
    session.commit()
    return chain


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestMitreMappingService:

    def test_map_known_event(self, db_session):
        """Known events should return a valid MitreTechnique."""
        service = MitreMappingService(db=db_session)
        technique = service.map_event("PortScan")

        assert technique is not None
        assert technique.technique_id == "T1595"
        assert technique.name == "Active Scanning"
        assert technique.tactic == "Reconnaissance"
        assert technique.event == "PortScan"

    def test_map_unknown_event_returns_none(self, db_session):
        """Unknown events should return None (not crash)."""
        service = MitreMappingService(db=db_session)
        technique = service.map_event("CompletelyUnknownEvent")

        assert technique is None

    def test_map_attack_chain_all_known(self, db_session):
        """Chain with all known events maps every event."""
        chain = _create_chain(db_session, "AC001", "PortScan,BruteForce,CredentialDumping,CommandExecution")
        service = MitreMappingService(db=db_session)

        mapping = service.map_attack_chain(chain)

        assert mapping.chain_id == "AC001"
        assert mapping.techniques_found == 4
        assert len(mapping.unmapped_events) == 0

        technique_ids = {t.technique_id for t in mapping.techniques}
        assert "T1595" in technique_ids  # PortScan
        assert "T1110" in technique_ids  # BruteForce
        assert "T1003" in technique_ids  # CredentialDumping
        assert "T1059" in technique_ids  # CommandExecution

    def test_map_attack_chain_with_unknown_events(self, db_session):
        """Chain with some unknown events should track them in unmapped_events."""
        chain = _create_chain(db_session, "AC002", "PortScan,WeirdEvent,BruteForce")
        service = MitreMappingService(db=db_session)

        mapping = service.map_attack_chain(chain)

        assert mapping.techniques_found == 2
        assert "WeirdEvent" in mapping.unmapped_events

    def test_map_attack_chain_deduplicates_techniques(self, db_session):
        """If two events map to the same technique_id, only one entry should appear."""
        # CommandExecution and RemoteCodeExecution both map to T1059
        chain = _create_chain(db_session, "AC003", "CommandExecution,RemoteCodeExecution")
        service = MitreMappingService(db=db_session)

        mapping = service.map_attack_chain(chain)

        assert mapping.techniques_found == 1
        assert mapping.techniques[0].technique_id == "T1059"

    def test_store_and_retrieve_mappings(self, db_session):
        """Mappings should persist to DB and be retrievable."""
        chain = _create_chain(db_session, "AC004", "PortScan,BruteForce")
        service = MitreMappingService(db=db_session)

        mapping = service.map_attack_chain(chain)
        stored_count = service.store_mappings(chain, mapping)
        assert stored_count == 2

        # Retrieve from DB
        retrieved = service.get_chain_mappings("AC004")
        assert retrieved.chain_id == "AC004"
        assert retrieved.techniques_found == 2

    def test_store_mappings_replaces_existing(self, db_session):
        """Re-storing mappings for the same chain should replace old ones."""
        chain = _create_chain(db_session, "AC005", "PortScan")
        service = MitreMappingService(db=db_session)

        # First store
        mapping = service.map_attack_chain(chain)
        service.store_mappings(chain, mapping)
        assert service.repo.count_mappings() == 1

        # Store again – should replace, not duplicate
        service.store_mappings(chain, mapping)
        assert service.repo.count_mappings() == 1

    def test_map_single_chain_endpoint_logic(self, db_session):
        """map_single_chain should return a success response."""
        _create_chain(db_session, "AC006", "PortScan,DataExfiltration")
        service = MitreMappingService(db=db_session)

        response = service.map_single_chain("AC006")

        assert response.success is True
        assert response.chain_id == "AC006"
        assert response.techniques_found == 2

    def test_map_single_chain_not_found(self, db_session):
        """Mapping a non-existent chain should raise MitreMappingError."""
        service = MitreMappingService(db=db_session)

        with pytest.raises(MitreMappingError, match="not found"):
            service.map_single_chain("AC_NONEXISTENT")

    def test_map_all_chains(self, db_session):
        """map_all_chains should process every chain in the database."""
        _create_chain(db_session, "AC007", "PortScan,BruteForce")
        _create_chain(db_session, "AC008", "Malware,DataExfiltration")
        service = MitreMappingService(db=db_session)

        result = service.map_all_chains()

        assert result.success is True
        assert result.chains_mapped == 2
        assert result.total_techniques >= 4
        assert result.execution_time_ms >= 0

    def test_map_all_chains_empty_db(self, db_session):
        """map_all_chains with no chains should raise MitreMappingError."""
        service = MitreMappingService(db=db_session)

        with pytest.raises(MitreMappingError, match="No attack chains found"):
            service.map_all_chains()

    def test_all_knowledge_base_entries_have_required_fields(self):
        """Every entry in MITRE_KNOWLEDGE_BASE must have technique_id and name."""
        for event_name, entry in MITRE_KNOWLEDGE_BASE.items():
            assert "technique_id" in entry, f"Missing technique_id for event '{event_name}'"
            assert "name" in entry, f"Missing name for event '{event_name}'"
            assert entry["technique_id"].startswith("T"), (
                f"Invalid technique_id '{entry['technique_id']}' for event '{event_name}'"
            )
