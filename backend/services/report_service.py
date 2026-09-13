"""
Report Service – coordinates context extraction, caching, LLM generation,
validation, and database persistence for Executive BLUF Reports.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from agents.bluf_report_agent import BlufReportAgent
from database.models import AttackChainDB, ReportDB
from repositories.attack_chain_repository import AttackChainRepository
from repositories.mitre_repository import MitreRepository
from repositories.risk_repository import RiskRepository
from repositories.recommendation_repository import RecommendationRepository
from repositories.report_repository import ReportRepository
from schemas.report import BlufReportOutput
from services.risk_scoring import RiskScoringEngine, ChainNotFoundError
from services.recommendation_service import RecommendationService

logger = logging.getLogger("report_service")


class ReportServiceError(Exception):
    """Base exception for report service errors."""
    pass


class ReportService:
    """
    Coordinates context extraction, LLM prompt engineering, BLUF report generation,
    caching, and database persistence.
    """

    def __init__(self, db: Session, agent: Optional[BlufReportAgent] = None):
        self.db = db
        self.chain_repo = AttackChainRepository(db)
        self.mitre_repo = MitreRepository(db)
        self.risk_repo = RiskRepository(db)
        self.rec_repo = RecommendationRepository(db)
        self.report_repo = ReportRepository(db)
        self.agent = agent or BlufReportAgent()

    def build_prompt(
        self,
        chain_id: str,
        events: List[str],
        source_ip: str,
        destination_ips: List[str],
        mitre_techniques: List[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
        reasoning: List[str],
        recommendations: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """Expose prompt construction for inspection and testing."""
        sys_prompt = self.agent.build_system_prompt()
        human_prompt = self.agent.build_human_prompt(
            chain_id=chain_id,
            events=events,
            source_ip=source_ip,
            destination_ips=destination_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
            reasoning=reasoning,
            recommendations=recommendations,
        )
        return sys_prompt, human_prompt

    def validate_report(self, data: Any, chain_id: str, default_threat_level: str = "Medium") -> BlufReportOutput:
        """Validate raw dictionary, string, or BlufReportOutput."""
        if isinstance(data, str):
            return self.agent.parse_and_validate(data, chain_id, default_threat_level)
        elif isinstance(data, dict):
            if not data.get("chain_id"):
                data["chain_id"] = chain_id
            if not data.get("threat_level"):
                data["threat_level"] = default_threat_level
            return BlufReportOutput.model_validate(data)
        elif isinstance(data, BlufReportOutput):
            return data
        raise ReportServiceError(f"Invalid report payload type: {type(data)}")

    def store_report(self, attack_chain_id: UUID, output: BlufReportOutput) -> ReportDB:
        """Persist executive BLUF report in database."""
        return self.report_repo.create_or_update_report(
            attack_chain_id=attack_chain_id,
            threat_level=output.threat_level,
            executive_summary=output.executive_summary,
            attack_overview=output.attack_overview,
            affected_assets=output.affected_assets,
            mitre_summary=output.mitre_summary,
            risk_assessment=output.risk_assessment,
            recommended_actions=output.recommended_actions,
            conclusion=output.conclusion,
        )

    def get_report(self, chain_id_str: str) -> Optional[BlufReportOutput]:
        """Retrieve existing report from database cache."""
        chain = self.chain_repo.get_chain(chain_id_str)
        if not chain:
            raise ChainNotFoundError(f"Attack chain '{chain_id_str}' not found")

        record = self.report_repo.get_report(chain.id)
        if not record:
            return None

        return BlufReportOutput(
            chain_id=chain.chain_id,
            threat_level=record.threat_level,
            executive_summary=record.executive_summary,
            attack_overview=record.attack_overview,
            affected_assets=record.affected_assets,
            mitre_summary=record.mitre_summary,
            risk_assessment=record.risk_assessment,
            recommended_actions=record.recommended_actions,
            conclusion=record.conclusion,
        )

    def get_all_reports(self, limit: int = 100, offset: int = 0) -> List[BlufReportOutput]:
        """Retrieve all stored BLUF reports from database."""
        records = self.report_repo.get_all_reports(limit=limit, offset=offset)
        results: List[BlufReportOutput] = []
        for r in records:
            chain = self.chain_repo.get_chain_by_uuid(r.attack_chain_id)
            chain_id_val = chain.chain_id if chain else str(r.attack_chain_id)
            results.append(
                BlufReportOutput(
                    chain_id=chain_id_val,
                    threat_level=r.threat_level,
                    executive_summary=r.executive_summary,
                    attack_overview=r.attack_overview,
                    affected_assets=r.affected_assets,
                    mitre_summary=r.mitre_summary,
                    risk_assessment=r.risk_assessment,
                    recommended_actions=r.recommended_actions,
                    conclusion=r.conclusion,
                )
            )
        return results

    def generate_report(
        self, chain_id_str: str, force_refresh: bool = False
    ) -> Tuple[BlufReportOutput, bool]:
        """
        Generate or retrieve cached BLUF report for an attack chain.
        Returns tuple: (BlufReportOutput, is_cached: bool)
        """
        start_time = time.perf_counter()
        logger.info(f"BLUF report requested for chain {chain_id_str} (force_refresh={force_refresh})")

        chain = self.chain_repo.get_chain(chain_id_str)
        if not chain:
            raise ChainNotFoundError(f"Attack chain '{chain_id_str}' not found")

        # 1. Check cache first
        if not force_refresh:
            existing = self.get_report(chain_id_str)
            if existing:
                logger.info(f"Serving cached BLUF report for chain {chain_id_str}")
                return existing, True

        # 2. Extract events
        events: List[str] = []
        if chain.events:
            events = [e.strip() for e in chain.events.split(",") if e.strip()]

        # 3. Extract destination IPs
        dest_ips: List[str] = []
        if chain.destination_ips:
            dest_ips = [d.strip() for d in chain.destination_ips.split(",") if d.strip()]

        # 4. Extract MITRE techniques
        mitre_db_mappings = self.mitre_repo.get_chain_mappings(chain.id)
        mitre_techniques: List[Dict[str, Any]] = [
            {
                "technique_id": m.technique_id,
                "name": m.technique_name,
                "tactic": m.tactic or "Unknown",
            }
            for m in mitre_db_mappings
        ]

        # 5. Extract or calculate Risk Score
        risk_record = self.risk_repo.get_by_chain_id(chain.id)
        if risk_record:
            risk_score = risk_record.score
            risk_level = risk_record.level
            reasoning = json.loads(risk_record.reasoning) if risk_record.reasoning else []
        else:
            logger.info(f"Risk score missing for chain {chain_id_str}. Auto-calculating.")
            risk_engine = RiskScoringEngine(self.db)
            score_obj = risk_engine.calculate_and_store_for_chain(chain_id_str)
            risk_score = score_obj.score
            risk_level = score_obj.level
            reasoning = score_obj.reasoning

        # 6. Extract or generate Recommendations
        rec_record = self.rec_repo.get_recommendation(chain.id)
        rec_data = None
        if rec_record:
            rec_data = {
                "immediate_actions": json.loads(rec_record.immediate_actions) if rec_record.immediate_actions else [],
                "containment_actions": json.loads(rec_record.containment_actions) if rec_record.containment_actions else [],
            }
        else:
            logger.info(f"Recommendations missing for chain {chain_id_str}. Auto-generating.")
            rec_service = RecommendationService(self.db)
            rec_obj, _ = rec_service.generate_recommendation(chain_id_str)
            rec_data = {
                "immediate_actions": rec_obj.immediate_actions,
                "containment_actions": rec_obj.containment_actions,
            }

        # 7. Generate via BlufReportAgent
        output = self.agent.generate(
            chain_id=chain.chain_id,
            events=events,
            source_ip=chain.source_ip,
            destination_ips=dest_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
            reasoning=reasoning,
            recommendations=rec_data,
        )

        # 8. Store in database
        self.store_report(chain.id, output)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Generated & stored BLUF report for chain {chain_id_str} in {elapsed_ms:.2f}ms")
        return output, False
