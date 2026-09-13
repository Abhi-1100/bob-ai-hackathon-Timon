"""
Repository for persisting and retrieving Attack Chains and their event associations.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import AttackChainDB, AttackChainEventDB

logger = logging.getLogger("attack_chain_repository")


class AttackChainRepository:
    """Encapsulates database interactions for AttackChain entities."""

    def __init__(self, db: Session):
        self.db = db

    def create_chain(
        self,
        chain_id: str,
        source_ip: str,
        destination_ips: str,
        events: str,
        alert_count: int,
        start_time,
        end_time,
        commit: bool = True,
    ) -> AttackChainDB:
        """Create and persist a new attack chain record.

        Args:
            chain_id: Human-readable identifier (e.g. AC001).
            source_ip: Common source IP for the chain.
            destination_ips: Comma-separated destination IPs.
            events: Comma-separated event progression.
            alert_count: Total alerts in this chain.
            start_time: Earliest alert timestamp.
            end_time: Latest alert timestamp.
            commit: Whether to commit immediately (False for bulk batching).
        """
        chain = AttackChainDB(
            chain_id=chain_id,
            source_ip=source_ip,
            destination_ips=destination_ips,
            events=events,
            alert_count=alert_count,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add(chain)
        if commit:
            try:
                self.db.commit()
                self.db.refresh(chain)
                logger.info(f"Attack chain '{chain_id}' created with {alert_count} alerts")
            except SQLAlchemyError as exc:
                self.db.rollback()
                raise RuntimeError(f"Failed to create attack chain '{chain_id}': {exc}")
        return chain

    def add_alert_to_chain(self, chain_db_id: UUID, alert_id: UUID) -> AttackChainEventDB:
        """Link an alert to an attack chain via the junction table."""
        event = AttackChainEventDB(chain_id=chain_db_id, alert_id=alert_id)
        self.db.add(event)
        return event

    def bulk_add_alerts_to_chain(self, chain_db_id: UUID, alert_ids: List[UUID], commit: bool = True) -> int:
        """Bulk-link multiple alerts to a chain. Returns count of links created."""
        events = [
            AttackChainEventDB(chain_id=chain_db_id, alert_id=aid)
            for aid in alert_ids
        ]
        self.db.bulk_save_objects(events)
        if commit:
            try:
                self.db.commit()
            except SQLAlchemyError as exc:
                self.db.rollback()
                raise RuntimeError(f"Failed to bulk-link alerts to chain {chain_db_id}: {exc}")
        return len(events)

    def get_chain(self, chain_id: str) -> Optional[AttackChainDB]:
        """Retrieve an attack chain by its human-readable chain_id (e.g. AC001)."""
        return (
            self.db.query(AttackChainDB)
            .filter(AttackChainDB.chain_id == chain_id)
            .first()
        )

    get_by_chain_id = get_chain

    def get_chain_by_uuid(self, chain_uuid: UUID) -> Optional[AttackChainDB]:
        """Retrieve an attack chain by its database UUID primary key."""
        return self.db.get(AttackChainDB, chain_uuid)

    def get_all_chains(self, limit: int = 200, offset: int = 0) -> List[AttackChainDB]:
        """Return all attack chains ordered by start_time, paginated."""
        return (
            self.db.query(AttackChainDB)
            .order_by(AttackChainDB.start_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete_chain(self, chain_id: str) -> None:
        """Delete an attack chain and cascade-delete its event links.

        Raises:
            ValueError: If the chain does not exist.
        """
        chain = self.get_chain(chain_id)
        if not chain:
            raise ValueError(f"Attack chain '{chain_id}' not found")
        self.db.delete(chain)
        try:
            self.db.commit()
            logger.info(f"Attack chain '{chain_id}' deleted")
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete attack chain '{chain_id}': {exc}")

    def delete_all_chains(self) -> int:
        """Delete all attack chains and their event links. Returns count deleted."""
        count = self.db.query(AttackChainDB).count()
        self.db.query(AttackChainEventDB).delete()
        self.db.query(AttackChainDB).delete()
        try:
            self.db.commit()
            logger.info(f"Deleted all {count} attack chains")
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete all attack chains: {exc}")
        return count

    def count_chains(self) -> int:
        """Return total number of attack chains stored."""
        return self.db.query(AttackChainDB).count()
