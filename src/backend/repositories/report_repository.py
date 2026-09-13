"""
Repository for persisting and retrieving Executive BLUF Threat Intelligence Reports.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import ReportDB

logger = logging.getLogger("report_repository")


class ReportRepository:
    """Encapsulates database operations for Report entities."""

    def __init__(self, db: Session):
        self.db = db

    def create_or_update_report(
        self,
        attack_chain_id: UUID,
        threat_level: str,
        executive_summary: str,
        attack_overview: str,
        affected_assets: str,
        mitre_summary: str,
        risk_assessment: str,
        recommended_actions: str,
        conclusion: str,
    ) -> ReportDB:
        """
        Create or update an executive report for a given attack chain.
        Maintains 1-to-1 relationship with upsert semantics.
        """
        existing = self.get_report(attack_chain_id)

        try:
            if existing:
                existing.threat_level = threat_level
                existing.executive_summary = executive_summary
                existing.attack_overview = attack_overview
                existing.affected_assets = affected_assets
                existing.mitre_summary = mitre_summary
                existing.risk_assessment = risk_assessment
                existing.recommended_actions = recommended_actions
                existing.conclusion = conclusion
                record = existing
            else:
                record = ReportDB(
                    attack_chain_id=attack_chain_id,
                    threat_level=threat_level,
                    executive_summary=executive_summary,
                    attack_overview=attack_overview,
                    affected_assets=affected_assets,
                    mitre_summary=mitre_summary,
                    risk_assessment=risk_assessment,
                    recommended_actions=recommended_actions,
                    conclusion=conclusion,
                )
                self.db.add(record)

            self.db.commit()
            self.db.refresh(record)
            logger.info(f"BLUF report saved for chain UUID {attack_chain_id}")
            return record

        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error(f"Failed to persist report for chain {attack_chain_id}: {exc}")
            raise RuntimeError(f"Database error saving BLUF report: {exc}")

    # Aliases to satisfy repository interface requirements
    create_report = create_or_update_report
    update_report = create_or_update_report

    def get_report(self, attack_chain_id: UUID) -> Optional[ReportDB]:
        """Retrieve executive report record for an attack chain UUID."""
        return (
            self.db.query(ReportDB)
            .filter(ReportDB.attack_chain_id == attack_chain_id)
            .first()
        )

    def get_all_reports(self, limit: int = 100, offset: int = 0) -> List[ReportDB]:
        """Retrieve all executive reports ordered by created_at descending."""
        return (
            self.db.query(ReportDB)
            .order_by(ReportDB.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def delete_report(self, attack_chain_id: UUID) -> bool:
        """Delete report for an attack chain. Returns True if deleted."""
        deleted = (
            self.db.query(ReportDB)
            .filter(ReportDB.attack_chain_id == attack_chain_id)
            .delete()
        )
        try:
            self.db.commit()
            return deleted > 0
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete report: {exc}")

    def delete_all_reports(self) -> int:
        """Delete all reports. Returns count deleted."""
        count = self.db.query(ReportDB).delete()
        try:
            self.db.commit()
            return count
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete all reports: {exc}")

    def count_reports(self) -> int:
        """Return total number of reports stored."""
        return self.db.query(ReportDB).count()
