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
        user_id: Optional[UUID] = None,
        commit: bool = True,
    ) -> AttackChainDB:
        """Create and persist a new attack chain record."""
        chain = AttackChainDB(
            user_id=user_id,
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
                logger.info(f"Attack chain '{chain_id}' created with {alert_count} alerts (user_id={user_id})")
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

    def get_chain(self, chain_id: str, user_id: Optional[UUID] = None) -> Optional[AttackChainDB]:
        """Retrieve an attack chain by its human-readable chain_id (e.g. AC001), optionally scoped to a user."""
        query = self.db.query(AttackChainDB).filter(AttackChainDB.chain_id == chain_id)
        if user_id:
            query = query.filter((AttackChainDB.user_id == user_id) | (AttackChainDB.user_id.is_(None)))
        return query.first()

    get_by_chain_id = get_chain

    def get_chain_by_uuid(self, chain_uuid: UUID, user_id: Optional[UUID] = None) -> Optional[AttackChainDB]:
        """Retrieve an attack chain by its database UUID primary key."""
        query = self.db.query(AttackChainDB).filter(AttackChainDB.id == chain_uuid)
        if user_id:
            query = query.filter((AttackChainDB.user_id == user_id) | (AttackChainDB.user_id.is_(None)))
        return query.first()

    def get_all_chains(self, limit: int = 200, offset: int = 0, user_id: Optional[UUID] = None) -> List[AttackChainDB]:
        """Return all attack chains ordered by start_time, paginated, optionally scoped to a user."""
        query = self.db.query(AttackChainDB)
        if user_id:
            query = query.filter((AttackChainDB.user_id == user_id) | (AttackChainDB.user_id.is_(None)))
        return (
            query.order_by(AttackChainDB.start_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete_chain(self, chain_id: str, user_id: Optional[UUID] = None) -> None:
        """Delete an attack chain and cascade-delete its event links."""
        chain = self.get_chain(chain_id, user_id=user_id)
        if not chain:
            raise ValueError(f"Attack chain '{chain_id}' not found")
        self.db.delete(chain)
        try:
            self.db.commit()
            logger.info(f"Attack chain '{chain_id}' deleted")
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete attack chain '{chain_id}': {exc}")

    def delete_all_chains(self, user_id: Optional[UUID] = None) -> int:
        """Delete attack chains. If user_id is provided, deletes only that user's chains."""
        query = self.db.query(AttackChainDB)
        if user_id:
            query = query.filter(AttackChainDB.user_id == user_id)
        chains = query.all()
        chain_ids = [c.id for c in chains]
        if not chain_ids:
            return 0
        self.db.query(AttackChainEventDB).filter(AttackChainEventDB.chain_id.in_(chain_ids)).delete(synchronize_session=False)
        count = query.delete(synchronize_session=False)
        try:
            self.db.commit()
            logger.info(f"Deleted {count} attack chains (user_id={user_id})")
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete attack chains: {exc}")
        return count

    def count_chains(self, user_id: Optional[UUID] = None) -> int:
        """Return total number of attack chains stored, optionally scoped to a user."""
        query = self.db.query(AttackChainDB)
        if user_id:
            query = query.filter(AttackChainDB.user_id == user_id)
        return query.count()
