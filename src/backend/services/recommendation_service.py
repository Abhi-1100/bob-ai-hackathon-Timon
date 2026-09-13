"""
Recommendation Service – orchestrates attack chain context retrieval,
caching, LLM generation, validation, and database storage.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from agents.recommendation_agent import RecommendationAgent
from database.models import AttackChainDB, RecommendationDB
from repositories.attack_chain_repository import AttackChainRepository
from repositories.mitre_repository import MitreRepository
from repositories.risk_repository import RiskRepository
from repositories.recommendation_repository import RecommendationRepository
from schemas.recommendation import RecommendationOutput
from services.risk_scoring import RiskScoringEngine, ChainNotFoundError

logger = logging.getLogger("recommendation_service")


class RecommendationServiceError(Exception):
    """Base exception for recommendation service errors."""
    pass


class RecommendationService:
    """
    Coordinates context extraction, LLM prompt engineering, recommendation generation,
    caching, and database persistence.
    """

    def __init__(self, db: Session, agent: Optional[RecommendationAgent] = None):
        self.db = db
        self.chain_repo = AttackChainRepository(db)
        self.mitre_repo = MitreRepository(db)
        self.risk_repo = RiskRepository(db)
        self.rec_repo = RecommendationRepository(db)
        self.agent = agent or RecommendationAgent()

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
    ) -> Tuple[str, str]:
        """Expose prompt construction for inspection and testing."""
        sys_prompt = self.agent.build_system_prompt()
        user_prompt = self.agent.build_human_prompt(
            chain_id=chain_id,
            events=events,
            source_ip=source_ip,
            destination_ips=destination_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
            reasoning=reasoning,
        )
        return sys_prompt, user_prompt

    def validate_response(self, data: Any, chain_id: str) -> RecommendationOutput:
        """Validate raw dictionary or text response into RecommendationOutput."""
        if isinstance(data, str):
            return self.agent.parse_and_validate(data, chain_id)
        elif isinstance(data, dict):
            if not data.get("chain_id"):
                data["chain_id"] = chain_id
            return RecommendationOutput.model_validate(data)
        elif isinstance(data, RecommendationOutput):
            return data
        raise RecommendationServiceError(f"Invalid recommendation payload type: {type(data)}")

    def store_recommendation(
        self, attack_chain_id: UUID, output: RecommendationOutput
    ) -> RecommendationDB:
        """Persist recommendation in database."""
        return self.rec_repo.create_or_update_recommendation(
            attack_chain_id=attack_chain_id,
            immediate_actions=output.immediate_actions,
            containment_actions=output.containment_actions,
            investigation_actions=output.investigation_actions,
            prevention_actions=output.prevention_actions,
            executive_summary=output.executive_summary,
        )

    def get_recommendation(self, chain_id_str: str) -> Optional[RecommendationOutput]:
        """Retrieve existing recommendation from database cache."""
        chain = self.chain_repo.get_chain(chain_id_str)
        if not chain:
            raise ChainNotFoundError(f"Attack chain '{chain_id_str}' not found")

        record = self.rec_repo.get_recommendation(chain.id)
        if not record:
            return None

        return RecommendationOutput(
            chain_id=chain.chain_id,
            immediate_actions=json.loads(record.immediate_actions),
            containment_actions=json.loads(record.containment_actions),
            investigation_actions=json.loads(record.investigation_actions),
            prevention_actions=json.loads(record.prevention_actions),
            executive_summary=record.executive_summary,
        )

    def generate_recommendation(
        self, chain_id_str: str, force_refresh: bool = False
    ) -> Tuple[RecommendationOutput, bool]:
        """
        Generate or retrieve cached security recommendations for an attack chain.
        Returns tuple: (RecommendationOutput, is_cached: bool)
        """
        start_time = time.perf_counter()
        logger.info(f"Recommendation requested for chain {chain_id_str} (force_refresh={force_refresh})")

        chain = self.chain_repo.get_chain(chain_id_str)
        if not chain:
            raise ChainNotFoundError(f"Attack chain '{chain_id_str}' not found")

        # 1. Check cache if not forcing refresh
        if not force_refresh:
            existing = self.get_recommendation(chain_id_str)
            if existing:
                logger.info(f"Serving cached recommendation for chain {chain_id_str}")
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
            # Auto-calculate risk score if not yet scored
            logger.info(f"Risk score missing for chain {chain_id_str}. Auto-calculating.")
            risk_engine = RiskScoringEngine(self.db)
            score_obj = risk_engine.calculate_and_store_for_chain(chain_id_str)
            risk_score = score_obj.score
            risk_level = score_obj.level
            reasoning = score_obj.reasoning

        # 6. Generate via RecommendationAgent
        output = self.agent.generate(
            chain_id=chain.chain_id,
            events=events,
            source_ip=chain.source_ip,
            destination_ips=dest_ips,
            mitre_techniques=mitre_techniques,
            risk_score=risk_score,
            risk_level=risk_level,
            reasoning=reasoning,
        )

        # 7. Store in database
        self.store_recommendation(chain.id, output)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Generated & stored recommendation for chain {chain_id_str} in {elapsed_ms:.2f}ms")
        return output, False

    def generate_all_recommendations(
        self, force_refresh: bool = False
    ) -> List[Tuple[RecommendationOutput, bool]]:
        """
        Generate recommendations for all attack chains in database.
        Returns list of tuples: (RecommendationOutput, is_cached)
        """
        chains = self.chain_repo.get_all_chains()
        results: List[Tuple[RecommendationOutput, bool]] = []
        for c in chains:
            res, cached = self.generate_recommendation(c.chain_id, force_refresh=force_refresh)
            results.append((res, cached))
        return results
