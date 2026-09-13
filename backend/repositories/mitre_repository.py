"""
Repository for persisting and retrieving MITRE ATT&CK technique mappings.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import MitreMappingDB

logger = logging.getLogger("mitre_repository")


class MitreRepository:
    """Encapsulates database interactions for MITRE ATT&CK mapping entities."""

    def __init__(self, db: Session):
        self.db = db

    def create_mapping(
        self,
        attack_chain_id: UUID,
        technique_id: str,
        technique_name: str,
        tactic: str = "Unknown",
        event: str = "",
    ) -> MitreMappingDB:
        """Create and persist a single MITRE technique mapping."""
        mapping = MitreMappingDB(
            attack_chain_id=attack_chain_id,
            technique_id=technique_id,
            technique_name=technique_name,
            tactic=tactic,
            event=event,
        )
        self.db.add(mapping)
        try:
            self.db.commit()
            self.db.refresh(mapping)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to create MITRE mapping: {exc}")
        return mapping

    def bulk_create_mappings(self, mappings: List[MitreMappingDB]) -> int:
        """Bulk-insert a list of MITRE mapping objects. Returns count of rows inserted."""
        self.db.bulk_save_objects(mappings)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Bulk insert of MITRE mappings failed: {exc}")
        return len(mappings)

    def get_chain_mappings(self, attack_chain_id: UUID) -> List[MitreMappingDB]:
        """Retrieve all MITRE mappings for a given attack chain UUID."""
        return (
            self.db.query(MitreMappingDB)
            .filter(MitreMappingDB.attack_chain_id == attack_chain_id)
            .order_by(MitreMappingDB.technique_id)
            .all()
        )

    def get_mapping_by_technique(self, technique_id: str) -> List[MitreMappingDB]:
        """Retrieve all mappings for a specific MITRE technique ID across all chains."""
        return (
            self.db.query(MitreMappingDB)
            .filter(MitreMappingDB.technique_id == technique_id)
            .all()
        )

    def delete_chain_mappings(self, attack_chain_id: UUID) -> int:
        """Delete all MITRE mappings for a chain. Returns count deleted."""
        count = (
            self.db.query(MitreMappingDB)
            .filter(MitreMappingDB.attack_chain_id == attack_chain_id)
            .delete()
        )
        try:
            self.db.commit()
            logger.info(f"Deleted {count} MITRE mappings for chain {attack_chain_id}")
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete MITRE mappings: {exc}")
        return count

    def delete_all_mappings(self) -> int:
        """Delete all MITRE mappings. Returns count deleted."""
        count = self.db.query(MitreMappingDB).delete()
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete all MITRE mappings: {exc}")
        return count

    def count_mappings(self) -> int:
        """Return total number of MITRE mapping records."""
        return self.db.query(MitreMappingDB).count()
