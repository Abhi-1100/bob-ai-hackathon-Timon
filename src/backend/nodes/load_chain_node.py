"""
Load Chain Node – retrieves attack chain data from PostgreSQL database.
"""

import logging
from typing import Optional
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from graph.state import ThreatWorkflowState
from repositories.attack_chain_repository import AttackChainRepository

logger = logging.getLogger("workflow.load_chain_node")


def load_chain_node(state: ThreatWorkflowState, config: Optional[RunnableConfig] = None) -> ThreatWorkflowState:
    """
    Fetch attack chain from database by chain_id.
    Stores structured attack_chain dictionary into workflow state.
    """
    chain_id = state.get("chain_id")
    logger.info(f"[Workflow Node: LoadChain] Loading attack chain {chain_id}")

    db: Session = state.get("_db")
    if not db and config:
        db = config.get("configurable", {}).get("db")
    if not db:
        from database.session import _get_session_factory
        db = _get_session_factory()()

    try:
        repo = AttackChainRepository(db)
        chain = repo.get_chain(chain_id, user_id=state.get("_user_id"))

        if not chain:
            error_msg = f"Attack chain '{chain_id}' not found in database."
            logger.error(f"[Workflow Node: LoadChain] {error_msg}")
            errors = list(state.get("errors", []))
            errors.append(error_msg)
            return {
                **state,
                "status": "failed",
                "errors": errors,
            }

        events_list = [e.strip() for e in chain.events.split(",") if e.strip()] if chain.events else []
        dest_list = [d.strip() for d in chain.destination_ips.split(",") if d.strip()] if chain.destination_ips else []

        attack_chain_data = {
            "id": str(chain.id),
            "chain_id": chain.chain_id,
            "source_ip": chain.source_ip,
            "destination_ips": dest_list,
            "events": events_list,
            "alert_count": chain.alert_count,
            "start_time": chain.start_time.isoformat() if chain.start_time else None,
            "end_time": chain.end_time.isoformat() if chain.end_time else None,
        }

        logger.info(f"[Workflow Node: LoadChain] Loaded chain {chain_id} with {chain.alert_count} alerts")
        return {
            **state,
            "attack_chain": attack_chain_data,
            "status": "in_progress",
        }

    except Exception as exc:
        error_msg = f"Failed to load attack chain '{chain_id}': {str(exc)}"
        logger.error(f"[Workflow Node: LoadChain] {error_msg}", exc_info=True)
        errors = list(state.get("errors", []))
        errors.append(error_msg)
        return {
            **state,
            "status": "failed",
            "errors": errors,
        }
