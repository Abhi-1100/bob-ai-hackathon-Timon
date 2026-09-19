"""
Repository for persisting and retrieving Risk Scores.
"""

import json
import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import RiskScoreDB

logger = logging.getLogger("risk_repository")


class RiskRepository:
    """Encapsulates database interactions for Risk Score entities."""

    def __init__(self, db: Session):
        self.db = db

    def save_risk_score(
        self,
        attack_chain_id: UUID,
        score: int,
        level: str,
        reasoning: List[str],
        event_score: int = 0,
        mitre_score: int = 0,
        chain_bonus: int = 0,
        behavioral_score: Optional[int] = None,
        behavioral_level: Optional[str] = None,
        commit: bool = True,
    ) -> RiskScoreDB:
        """
        Create or update a risk score for a specific attack chain.
        Ensures uniqueness per attack_chain_id (upsert behavior).
        """
        reasoning_json = json.dumps(reasoning)

        existing = (
            self.db.query(RiskScoreDB)
            .filter(RiskScoreDB.attack_chain_id == attack_chain_id)
            .first()
        )

        try:
            if existing:
                existing.score = score
                existing.level = level
                existing.reasoning = reasoning_json
                existing.event_score = event_score
                existing.mitre_score = mitre_score
                existing.chain_bonus = chain_bonus
                if behavioral_score is not None:
                    existing.behavioral_score = behavioral_score
                if behavioral_level is not None:
                    existing.behavioral_level = behavioral_level
                record = existing
            else:
                record = RiskScoreDB(
                    attack_chain_id=attack_chain_id,
                    score=score,
                    level=level,
                    reasoning=reasoning_json,
                    event_score=event_score,
                    mitre_score=mitre_score,
                    chain_bonus=chain_bonus,
                    behavioral_score=behavioral_score,
                    behavioral_level=behavioral_level,
                )
                self.db.add(record)

            if commit:
                self.db.commit()
                self.db.refresh(record)
            return record
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(f"Failed to save risk score for chain {attack_chain_id}: {exc}")
            raise RuntimeError(f"Database error saving risk score: {exc}")

    def get_by_chain_id(self, attack_chain_id: UUID) -> Optional[RiskScoreDB]:
        """Retrieve the risk score record for an attack chain UUID."""
        return (
            self.db.query(RiskScoreDB)
            .filter(RiskScoreDB.attack_chain_id == attack_chain_id)
            .first()
        )

    def get_all_scores(self) -> List[RiskScoreDB]:
        """Retrieve all risk scores ordered by score descending (highest risk first)."""
        return (
            self.db.query(RiskScoreDB)
            .order_by(RiskScoreDB.score.desc())
            .all()
        )

    def delete_by_chain_id(self, attack_chain_id: UUID) -> bool:
        """Delete risk score for a chain. Returns True if deleted."""
        deleted = (
            self.db.query(RiskScoreDB)
            .filter(RiskScoreDB.attack_chain_id == attack_chain_id)
            .delete()
        )
        try:
            self.db.commit()
            return deleted > 0
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete risk score: {exc}")

    def delete_all_scores(self) -> int:
        """Delete all risk scores. Returns count deleted."""
        count = self.db.query(RiskScoreDB).delete()
        try:
            self.db.commit()
            return count
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete all risk scores: {exc}")

    def count_scores(self) -> int:
        """Return total number of risk score records."""
        return self.db.query(RiskScoreDB).count()

    def get_distribution(self, user_id: Optional[UUID] = None) -> Dict[str, int]:
        """Return counts grouped by risk level (Critical, High, Medium, Low), optionally scoped to a user."""
        from database.models import AttackChainDB
        query = self.db.query(RiskScoreDB.level)
        if user_id:
            query = query.join(AttackChainDB, RiskScoreDB.attack_chain_id == AttackChainDB.id).filter(AttackChainDB.user_id == user_id)
        all_records = query.all()
        dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for (level,) in all_records:
            if level in dist:
                dist[level] += 1
            else:
                dist[level] = 1
        return dist
