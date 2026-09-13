"""
Production-Ready Risk Scoring Engine.

Deterministic, rule-based engine that calculates composite risk scores (0-100),
assigns severity levels (Low, Medium, High, Critical), and generates explainable reasoning
for correlated attack chains and their MITRE ATT&CK techniques.

This module does NOT use LLMs, LangGraph, or any AI.
All scoring is fully auditable, reproducible, and deterministic.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import AttackChainDB, MitreMappingDB
from repositories.attack_chain_repository import AttackChainRepository
from repositories.mitre_repository import MitreRepository
from repositories.risk_repository import RiskRepository
from schemas.risk_score import RiskScore, RiskDistribution

logger = logging.getLogger("risk_scoring")


class RiskScoringError(Exception):
    """Base exception for Risk Scoring engine errors."""
    pass


class ChainNotFoundError(RiskScoringError):
    """Raised when an attack chain is not found."""
    pass


# ---------------------------------------------------------------------------
# Scoring Constants & Weights
# ---------------------------------------------------------------------------

EVENT_WEIGHTS: Dict[str, int] = {
    "PortScan": 10,
    "BruteForce": 25,
    "CredentialDumping": 40,
    "PrivilegeEscalation": 45,
    "CommandExecution": 35,
    "Malware": 50,
    "Persistence": 35,
    "DataExfiltration": 70,
    # Extended common events
    "SQLInjection": 30,
    "Phishing": 20,
    "LateralMovement": 40,
    "C2Beacon": 35,
    "DDoS": 25,
    "Ransomware": 60,
}
DEFAULT_EVENT_WEIGHT: int = 10

MITRE_TACTIC_WEIGHTS: Dict[str, int] = {
    "Reconnaissance": 5,
    "Credential Access": 20,
    "Execution": 15,
    "Persistence": 15,
    "Exfiltration": 30,
    "Privilege Escalation": 20,
    "Defense Evasion": 15,
    "Lateral Movement": 20,
    "Command and Control": 15,
    "Impact": 25,
    "Initial Access": 10,
}


class RiskScoringEngine:
    """
    Deterministic risk scoring engine for threat intelligence attack chains.
    Calculates likelihood × impact based on event types, MITRE tactics, and chain progression.
    """

    def __init__(self, db: Session):
        self.db = db
        self.chain_repo = AttackChainRepository(db)
        self.mitre_repo = MitreRepository(db)
        self.risk_repo = RiskRepository(db)

    # -----------------------------------------------------------------------
    # Sub-scoring Methods
    # -----------------------------------------------------------------------

    def calculate_event_score(self, events: List[str]) -> Tuple[int, List[str]]:
        """
        Calculate sub-score from event weights based on unique event types observed.
        Returns (score, list of identified high-risk event explanations).
        """
        if not events:
            return 0, []

        score = 0
        explanations = []
        unique_events = set(events)

        for event in unique_events:
            weight = EVENT_WEIGHTS.get(event, DEFAULT_EVENT_WEIGHT)
            score += weight
            if event == "Malware":
                explanations.append("Malware activity detected")
            elif event in ("CredentialDumping", "BruteForce"):
                explanations.append("Credential theft behavior observed")
            elif event == "DataExfiltration":
                explanations.append("Data exfiltration activity detected")
            elif event == "PrivilegeEscalation":
                explanations.append("Privilege escalation attempt identified")
            elif event == "CommandExecution":
                explanations.append("Arbitrary command execution observed")

        return score, explanations

    def calculate_mitre_score(
        self, mappings: List[Any]
    ) -> Tuple[int, List[str]]:
        """
        Calculate sub-score from MITRE ATT&CK tactic weights.
        Deduplicates tactics to avoid unbounded score inflation from repeated tactics.
        Returns (score, list of MITRE-specific explanations).
        """
        if not mappings:
            return 0, []

        score = 0
        explanations = []
        seen_tactics: Set[str] = set()

        for m in mappings:
            tactic = getattr(m, "tactic", None) or (m.get("tactic") if isinstance(m, dict) else "Unknown")
            if tactic and tactic not in seen_tactics:
                seen_tactics.add(tactic)
                weight = MITRE_TACTIC_WEIGHTS.get(tactic, 0)
                score += weight

        if "Exfiltration" in seen_tactics:
            explanations.append("High-risk MITRE technique present: Exfiltration")
        if "Credential Access" in seen_tactics:
            explanations.append("High-risk MITRE technique present: Credential Access")
        if "Execution" in seen_tactics:
            explanations.append("MITRE Execution technique verified")
        if "Reconnaissance" in seen_tactics:
            explanations.append("Pre-attack reconnaissance phase observed")

        return score, explanations

    def calculate_chain_bonus(self, event_count: int) -> int:
        """
        Assign bonus points based on length / progression of the attack chain.
        - 7+ events: +20
        - 5+ events: +15
        - 3+ events: +10
        - <3 events: 0
        """
        if event_count >= 7:
            return 20
        elif event_count >= 5:
            return 15
        elif event_count >= 3:
            return 10
        return 0

    def calculate_total_score(
        self, event_score: int, mitre_score: int, chain_bonus: int
    ) -> int:
        """
        Calculate raw combined score and cap between 0 and 100.
        """
        raw = event_score + mitre_score + chain_bonus
        return min(100, max(0, raw))

    def determine_severity(self, score: int) -> str:
        """
        Assign standardized risk severity level based on final score:
        - 0 - 25: Low
        - 26 - 50: Medium
        - 51 - 75: High
        - 76 - 100: Critical
        """
        if score >= 76:
            return "Critical"
        elif score >= 51:
            return "High"
        elif score >= 26:
            return "Medium"
        return "Low"

    def generate_reasoning(
        self,
        event_explanations: List[str],
        mitre_explanations: List[str],
        chain_bonus: int,
        event_count: int,
        final_score: int,
        level: str,
    ) -> List[str]:
        """
        Assemble comprehensive, human-readable explanations for the score.
        Guarantees that every calculated score includes explicit reasons.
        """
        reasoning: List[str] = []

        # Event-specific explanations
        reasoning.extend(event_explanations)

        # MITRE-specific explanations
        reasoning.extend(mitre_explanations)

        # Chain progression explanation
        if chain_bonus > 0:
            reasoning.append(
                f"Multi-stage attack progression observed ({event_count} events, +{chain_bonus} bonus)"
            )
        elif event_count > 0:
            reasoning.append(f"Attack chain consists of {event_count} correlated event(s)")

        # Fallback if reasoning is somehow empty
        if not reasoning:
            reasoning.append(f"Standard baseline threat activity assessed (Score: {final_score})")

        # Summary justification line
        reasoning.append(f"Severity classified as {level} based on total risk score of {final_score}/100")

        return reasoning

    # -----------------------------------------------------------------------
    # Core Scoring Workflows
    # -----------------------------------------------------------------------

    def score_chain_data(
        self,
        chain_id: str,
        events: List[str],
        mitre_mappings: Optional[List[Any]] = None,
    ) -> RiskScore:
        """
        Pure calculation method without direct database dependency.
        Useful for standalone evaluations and unit tests.
        """
        event_score, event_expl = self.calculate_event_score(events)
        mitre_score, mitre_expl = self.calculate_mitre_score(mitre_mappings or [])
        chain_bonus = self.calculate_chain_bonus(len(events))

        total_score = self.calculate_total_score(event_score, mitre_score, chain_bonus)
        level = self.determine_severity(total_score)

        reasoning = self.generate_reasoning(
            event_explanations=event_expl,
            mitre_explanations=mitre_expl,
            chain_bonus=chain_bonus,
            event_count=len(events),
            final_score=total_score,
            level=level,
        )

        return RiskScore(
            chain_id=chain_id,
            score=total_score,
            level=level,
            reasoning=reasoning,
            event_score=event_score,
            mitre_score=mitre_score,
            chain_bonus=chain_bonus,
            metadata={
                "event_count": len(events),
                "unique_events": list(set(events)),
                "mitre_mappings_count": len(mitre_mappings or []),
            },
        )

    def calculate_and_store_for_chain(self, chain_id_str: str, commit: bool = True) -> RiskScore:
        """
        Calculate and persist risk score for a single chain identified by string ID.
        """
        start_time = time.perf_counter()
        chain = self.chain_repo.get_by_chain_id(chain_id_str)
        if not chain:
            raise ChainNotFoundError(f"Attack chain '{chain_id_str}' not found")

        # Extract events list from comma-separated string
        events: List[str] = []
        if chain.events:
            events = [e.strip() for e in chain.events.split(",") if e.strip()]

        # Load MITRE mappings associated with the chain
        mitre_mappings = self.mitre_repo.get_chain_mappings(chain.id)

        # Calculate score
        score_obj = self.score_chain_data(
            chain_id=chain.chain_id,
            events=events,
            mitre_mappings=mitre_mappings,
        )

        # Persist to database
        self.risk_repo.save_risk_score(
            attack_chain_id=chain.id,
            score=score_obj.score,
            level=score_obj.level,
            reasoning=score_obj.reasoning,
            event_score=score_obj.event_score,
            mitre_score=score_obj.mitre_score,
            chain_bonus=score_obj.chain_bonus,
            commit=commit,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Risk score stored for chain {chain.chain_id}: score={score_obj.score}, "
            f"level={score_obj.level} in {elapsed_ms:.2f}ms"
        )
        return score_obj

    def score_all_chains(self) -> List[RiskScore]:
        """
        Calculate and persist risk scores for ALL attack chains in the database.
        Returns list of scored chains ordered by score descending.
        """
        start_time = time.perf_counter()
        chains = self.chain_repo.get_all_chains(limit=2000)
        logger.info(f"Scoring all chains: {len(chains)} chains found")

        results: List[RiskScore] = []
        for chain in chains:
            score_obj = self.calculate_and_store_for_chain(chain.chain_id, commit=False)
            results.append(score_obj)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(f"Failed to commit bulk risk scores: {exc}")

        # Sort by score descending (highest priority attack chains first)
        results.sort(key=lambda r: r.score, reverse=True)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Completed scoring {len(results)} chains in {elapsed_ms:.2f}ms")
        return results

    def get_stored_score(self, chain_id_str: str) -> Optional[RiskScore]:
        """
        Retrieve existing calculated risk score from DB for a chain ID.
        """
        chain = self.chain_repo.get_by_chain_id(chain_id_str)
        if not chain:
            raise ChainNotFoundError(f"Attack chain '{chain_id_str}' not found")

        record = self.risk_repo.get_by_chain_id(chain.id)
        if not record:
            return None

        reasoning_list = []
        if record.reasoning:
            try:
                reasoning_list = json.loads(record.reasoning)
            except Exception:
                reasoning_list = [record.reasoning]

        return RiskScore(
            chain_id=chain.chain_id,
            score=record.score,
            level=record.level,
            reasoning=reasoning_list,
            event_score=record.event_score or 0,
            mitre_score=record.mitre_score or 0,
            chain_bonus=record.chain_bonus or 0,
            metadata={
                "created_at": record.created_at.isoformat() if record.created_at else None
            },
        )

    def get_risk_distribution(self) -> RiskDistribution:
        """
        Return count distribution across risk levels.
        """
        dist = self.risk_repo.get_distribution()
        total = sum(dist.values())
        return RiskDistribution(
            total_chains=total,
            critical=dist.get("Critical", 0),
            high=dist.get("High", 0),
            medium=dist.get("Medium", 0),
            low=dist.get("Low", 0),
        )
