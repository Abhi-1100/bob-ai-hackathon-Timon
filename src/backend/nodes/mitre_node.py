"""
MITRE Mapping Node – orchestrates deterministic MITRE ATT&CK mapping service.
"""

import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from graph.state import ThreatWorkflowState
from services.mitre_mapping import MitreMappingService

logger = logging.getLogger("workflow.mitre_node")


def mitre_node(state: ThreatWorkflowState, config: Optional[RunnableConfig] = None) -> ThreatWorkflowState:
    """
    Orchestrates the existing MITRE Mapping Service.
    Does NOT duplicate business logic; delegates mapping to MitreMappingService.
    """
    if state.get("status") == "failed":
        logger.warning("[Workflow Node: MITRE] Skipping node due to previous workflow failure")
        return state

    chain_id = state.get("chain_id")
    logger.info(f"[Workflow Node: MITRE] Mapping attack chain {chain_id} to MITRE ATT&CK")

    db: Session = state.get("_db")
    if not db and config:
        db = config.get("configurable", {}).get("db")
    if not db:
        from database.session import _get_session_factory
        db = _get_session_factory()()

    try:
        service = MitreMappingService(db=db)
        service.map_single_chain(chain_id)
        chain_mapping = service.get_chain_mappings(chain_id)

        techniques_data = [t.model_dump() for t in chain_mapping.techniques]
        logger.info(f"[Workflow Node: MITRE] Mapped {len(techniques_data)} techniques for chain {chain_id}")

        return {
            **state,
            "mitre_mappings": techniques_data,
        }

    except Exception as exc:
        error_msg = f"MITRE mapping failed for chain '{chain_id}': {str(exc)}"
        logger.error(f"[Workflow Node: MITRE] {error_msg}", exc_info=True)
        errors = list(state.get("errors", []))
        errors.append(error_msg)
        return {
            **state,
            "status": "failed",
            "errors": errors,
        }
