"""
Risk Scoring Node – orchestrates deterministic Risk Scoring Engine.
"""

import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from graph.state import ThreatWorkflowState
from services.risk_scoring import RiskScoringEngine

logger = logging.getLogger("workflow.risk_node")


def risk_node(state: ThreatWorkflowState, config: Optional[RunnableConfig] = None) -> ThreatWorkflowState:
    """
    Orchestrates the existing Risk Scoring Engine.
    Does NOT duplicate business logic; delegates scoring to RiskScoringEngine.
    """
    if state.get("status") == "failed":
        logger.warning("[Workflow Node: Risk] Skipping node due to previous workflow failure")
        return state

    chain_id = state.get("chain_id")
    logger.info(f"[Workflow Node: Risk] Calculating risk score for chain {chain_id}")

    db: Session = state.get("_db")
    if not db and config:
        db = config.get("configurable", {}).get("db")
    if not db:
        from database.session import _get_session_factory
        db = _get_session_factory()()

    try:
        engine = RiskScoringEngine(db=db)
        score_obj = engine.calculate_and_store_for_chain(chain_id)

        risk_data = {
            "score": score_obj.score,
            "level": score_obj.level,
            "reasoning": score_obj.reasoning,
            "event_score": score_obj.event_score,
            "mitre_score": score_obj.mitre_score,
            "chain_bonus": score_obj.chain_bonus,
        }
        logger.info(f"[Workflow Node: Risk] Assessed risk for {chain_id}: {score_obj.score}/100 ({score_obj.level})")

        return {
            **state,
            "risk_score": risk_data,
        }

    except Exception as exc:
        error_msg = f"Risk scoring failed for chain '{chain_id}': {str(exc)}"
        logger.error(f"[Workflow Node: Risk] {error_msg}", exc_info=True)
        errors = list(state.get("errors", []))
        errors.append(error_msg)
        return {
            **state,
            "status": "failed",
            "errors": errors,
        }
