"""
Behavioral Analysis Node - integrates behavioral anomaly scoring into LangGraph workflow.
"""

import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from graph.state import ThreatWorkflowState
from services.behavioral_analysis import BehavioralAnalysisEngine

logger = logging.getLogger("workflow.behavior_node")


def behavior_node(state: ThreatWorkflowState, config: Optional[RunnableConfig] = None) -> ThreatWorkflowState:
    """
    Executes the Behavioral + Context Analysis layer.
    """
    if state.get("status") == "failed":
        logger.warning("[Workflow Node: Behavior] Skipping node due to previous workflow failure")
        return state

    chain_id = state.get("chain_id")
    logger.info(f"[Workflow Node: Behavior] Running behavioral analysis for chain {chain_id}")

    db: Session = state.get("_db")
    if not db and config:
        db = config.get("configurable", {}).get("db")
    if not db:
        from database.session import _get_session_factory
        db = _get_session_factory()()

    user_id = state.get("_user_id")

    try:
        engine = BehavioralAnalysisEngine(db=db)
        result = engine.analyze_chain(chain_id, user_id=user_id)
        
        # Store result in state
        behavioral_data = result.model_dump()
        
        logger.info(f"[Workflow Node: Behavior] Assessed anomaly for {chain_id}: {result.anomaly_score}/100 ({result.anomaly_level})")

        return {
            **state,
            "behavioral_analysis": behavioral_data,
        }

    except Exception as exc:
        # We don't want behavioral analysis failure to completely halt the workflow,
        # so we log the error and continue without behavioral data.
        error_msg = f"Behavioral analysis failed for chain '{chain_id}': {str(exc)}"
        logger.error(f"[Workflow Node: Behavior] {error_msg}", exc_info=True)
        # We are intentionally NOT setting status="failed" here to allow graceful degradation
        return {
            **state,
            "behavioral_analysis": None,
        }
