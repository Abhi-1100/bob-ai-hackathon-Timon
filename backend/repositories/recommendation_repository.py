"""
Repository for persisting and retrieving LLM Security Recommendations.
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import RecommendationDB

logger = logging.getLogger("recommendation_repository")


class RecommendationRepository:
    """Encapsulates database operations for Recommendation entities."""

    def __init__(self, db: Session):
        self.db = db

    def create_or_update_recommendation(
        self,
        attack_chain_id: UUID,
        immediate_actions: List[str],
        containment_actions: List[str],
        investigation_actions: List[str],
        prevention_actions: List[str],
        executive_summary: str,
    ) -> RecommendationDB:
        """
        Create or update the recommendation for a given attack chain UUID.
        Maintains 1-to-1 relationship with upsert semantics.
        """
        imm_json = json.dumps(immediate_actions)
        cont_json = json.dumps(containment_actions)
        inv_json = json.dumps(investigation_actions)
        prev_json = json.dumps(prevention_actions)

        existing = self.get_recommendation(attack_chain_id)

        try:
            if existing:
                existing.immediate_actions = imm_json
                existing.containment_actions = cont_json
                existing.investigation_actions = inv_json
                existing.prevention_actions = prev_json
                existing.executive_summary = executive_summary
                record = existing
            else:
                record = RecommendationDB(
                    attack_chain_id=attack_chain_id,
                    immediate_actions=imm_json,
                    containment_actions=cont_json,
                    investigation_actions=inv_json,
                    prevention_actions=prev_json,
                    executive_summary=executive_summary,
                )
                self.db.add(record)

            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Recommendation saved for chain UUID {attack_chain_id}")
            return record

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(f"Failed to persist recommendation for chain {attack_chain_id}: {exc}")
            raise RuntimeError(f"Database error saving recommendation: {exc}")

    # Aliases to fulfill requirements
    create_recommendation = create_or_update_recommendation
    update_recommendation = create_or_update_recommendation

    def get_recommendation(self, attack_chain_id: UUID) -> Optional[RecommendationDB]:
        """Retrieve recommendation record for an attack chain UUID."""
        return (
            self.db.query(RecommendationDB)
            .filter(RecommendationDB.attack_chain_id == attack_chain_id)
            .first()
        )

    def delete_recommendation(self, attack_chain_id: UUID) -> bool:
        """Delete recommendation for an attack chain. Returns True if deleted."""
        deleted = (
            self.db.query(RecommendationDB)
            .filter(RecommendationDB.attack_chain_id == attack_chain_id)
            .delete()
        )
        try:
            self.db.commit()
            return deleted > 0
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete recommendation: {exc}")

    def delete_all_recommendations(self) -> int:
        """Delete all recommendations. Returns count deleted."""
        count = self.db.query(RecommendationDB).delete()
        try:
            self.db.commit()
            return count
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete all recommendations: {exc}")

    def count_recommendations(self) -> int:
        """Return total number of recommendation records stored."""
        return self.db.query(RecommendationDB).count()
