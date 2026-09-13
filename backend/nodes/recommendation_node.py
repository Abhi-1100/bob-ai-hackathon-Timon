"""
Recommendation Node – orchestrates LLM Recommendation Agent with automatic retries.
"""

import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from graph.state import ThreatWorkflowState
from services.recommendation_service import RecommendationService

logger = logging.getLogger("workflow.recommendation_node")

MAX_RETRIES = 3


def recommendation_node(state: ThreatWorkflowState, config: Optional[RunnableConfig] = None) -> ThreatWorkflowState:
    """
    Orchestrates the existing Recommendation Service.
    Retries up to 3 times on transient failures.
    Stores recommendation dictionary into state.
    """
    if state.get("status") == "failed":
        logger.warning("[Workflow Node: Recommendation] Skipping node due to previous failure")
        return state

    chain_id = state.get("chain_id")
    logger.info(f"[Workflow Node: Recommendation] Generating security recommendations for chain {chain_id}")

    db: Session = state.get("_db")
    if not db and config:
        db = config.get("configurable", {}).get("db")
    if not db:
        from database.session import _get_session_factory
        db = _get_session_factory()()

    service = RecommendationService(db=db)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            rec_output, is_cached = service.generate_recommendation(chain_id, force_refresh=False)
            logger.info(
                f"[Workflow Node: Recommendation] Successfully retrieved recommendations for {chain_id} "
                f"(cached={is_cached}, attempt={attempt})"
            )
            return {
                **state,
                "recommendations": rec_output.model_dump(),
            }
        except Exception as exc:
            last_error = exc
            logger.warning(
                f"[Workflow Node: Recommendation] Attempt {attempt}/{MAX_RETRIES} failed for chain {chain_id}: {exc}"
            )

    error_msg = f"Recommendation generation failed after {MAX_RETRIES} attempts: {str(last_error)}"
    logger.error(f"[Workflow Node: Recommendation] {error_msg}")
    errors = list(state.get("errors", []))
    errors.append(error_msg)
    return {
        **state,
        "status": "failed",
        "errors": errors,
    }
