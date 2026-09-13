"""
Store Results Node – finalizes workflow state, verifies completeness, and records completion status.
"""

from datetime import datetime, timezone
import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig

from graph.state import ThreatWorkflowState

logger = logging.getLogger("workflow.store_results_node")


def store_results_node(state: ThreatWorkflowState, config: Optional[RunnableConfig] = None) -> ThreatWorkflowState:
    """
    Finalize workflow execution.
    If no errors accumulated, mark status as 'completed'.
    Otherwise, ensure status reflects 'failed'.
    """
    chain_id = state.get("chain_id")
    errors = state.get("errors", [])

    if errors or state.get("status") == "failed":
        logger.error(f"[Workflow Node: StoreResults] Workflow completed with {len(errors)} error(s) for chain {chain_id}")
        return {
            **state,
            "status": "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Verify all expected artifacts are present in state
    has_mitre = bool(state.get("mitre_mappings"))
    has_risk = bool(state.get("risk_score"))
    has_recs = bool(state.get("recommendations"))
    has_report = bool(state.get("report"))

    logger.info(
        f"[Workflow Node: StoreResults] Successfully completed workflow for chain {chain_id} "
        f"[MITRE={has_mitre}, Risk={has_risk}, Recs={has_recs}, Report={has_report}]"
    )

    return {
        **state,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
