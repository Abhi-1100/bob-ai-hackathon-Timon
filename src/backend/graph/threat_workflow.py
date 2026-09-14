"""
LangGraph Threat Intelligence Workflow Orchestrator.
Orchestrates: LoadChain -> MITRE -> RiskScoring -> RecommendationAgent -> BLUFReportAgent -> StoreResults.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, START, END

from graph.state import ThreatWorkflowState
from nodes.load_chain_node import load_chain_node
from nodes.mitre_node import mitre_node
from nodes.risk_node import risk_node
from nodes.recommendation_node import recommendation_node
from nodes.report_node import report_node
from nodes.store_results_node import store_results_node

logger = logging.getLogger("workflow.orchestrator")


def should_continue(state: ThreatWorkflowState) -> str:
    """
    Conditional edge router.
    If any node failed, short-circuits to store_results to record failure and stop execution.
    """
    if state.get("status") == "failed" or state.get("errors"):
        logger.warning("[Workflow Router] Error detected in state. Short-circuiting to store_results.")
        return "store_results"
    return "continue"


def create_threat_workflow():
    """Build and compile the LangGraph StateGraph workflow."""
    workflow = StateGraph(ThreatWorkflowState)

    # Add orchestration nodes
    workflow.add_node("load_chain", load_chain_node)
    workflow.add_node("mitre_mapping", mitre_node)
    workflow.add_node("risk_scoring", risk_node)
    workflow.add_node("recommendations", recommendation_node)
    workflow.add_node("bluf_report", report_node)
    workflow.add_node("store_results", store_results_node)

    # Define linear graph edges with short-circuit failure routing
    workflow.add_edge(START, "load_chain")

    workflow.add_conditional_edges(
        "load_chain",
        should_continue,
        {
            "continue": "mitre_mapping",
            "store_results": "store_results",
        },
    )

    workflow.add_conditional_edges(
        "mitre_mapping",
        should_continue,
        {
            "continue": "risk_scoring",
            "store_results": "store_results",
        },
    )

    workflow.add_conditional_edges(
        "risk_scoring",
        should_continue,
        {
            "continue": "recommendations",
            "store_results": "store_results",
        },
    )

    workflow.add_conditional_edges(
        "recommendations",
        should_continue,
        {
            "continue": "bluf_report",
            "store_results": "store_results",
        },
    )

    workflow.add_edge("bluf_report", "store_results")
    workflow.add_edge("store_results", END)

    return workflow.compile()


# Global compiled instance
compiled_threat_workflow = create_threat_workflow()


class ThreatWorkflowRunner:
    """
    Production-ready runner for invoking the LangGraph workflow with
    session management, execution timing, and structured error reporting.
    """

    def __init__(self, db: Session, user_id: Optional[Any] = None):
        self.db = db
        self.user_id = user_id
        self.graph = compiled_threat_workflow

    def run(self, chain_id: str) -> ThreatWorkflowState:
        """
        Execute the end-to-end orchestration pipeline for a given attack chain.
        """
        start_time = time.perf_counter()
        logger.info(f"=== Starting LangGraph Threat Intelligence Workflow for {chain_id} ===")

        initial_state: ThreatWorkflowState = {
            "chain_id": chain_id,
            "attack_chain": None,
            "mitre_mappings": None,
            "risk_score": None,
            "recommendations": None,
            "report": None,
            "status": "in_progress",
            "errors": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_metadata": {"start_time": start_time},
            "_db": self.db,
            "_user_id": self.user_id,
        }

        # Provide db session through LangGraph RunnableConfig as well
        config = {"configurable": {"db": self.db}}

        final_state = self.graph.invoke(initial_state, config=config)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        status_result = final_state.get("status", "unknown")
        logger.info(
            f"=== LangGraph Workflow for {chain_id} finished in {elapsed_ms:.2f}ms "
            f"with status='{status_result}' ==="
        )

        # Store elapsed time in metadata
        metadata = dict(final_state.get("execution_metadata", {}))
        metadata["execution_time_ms"] = round(elapsed_ms, 2)
        final_state["execution_metadata"] = metadata

        return final_state
