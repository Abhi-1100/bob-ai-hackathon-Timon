"""
Retrieve Node for AI Analyst Chat System.
Embeds the user question and queries Qdrant for relevant threat intelligence documents.
"""

import logging
import time
from typing import Any, Dict, List

try:
    from services.qdrant_service import QdrantService
    from schemas.chat import ThreatDocSchema
except ImportError:
    from backend.services.qdrant_service import QdrantService
    from backend.schemas.chat import ThreatDocSchema

logger = logging.getLogger("threat_intelligence.nodes.retrieve")


def retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves top K threat intelligence documents matching the user query from Qdrant.
    Supports metadata filtering on risk, chain_id, and mitre technique.
    """
    start_time = time.time()
    question = state.get("question", "").strip()
    top_k = state.get("top_k", 5)
    filter_chain_id = state.get("filter_chain_id")
    filter_risk = state.get("filter_risk")
    filter_mitre = state.get("filter_mitre")

    logger.info("Question received: '%s'", question)
    logger.info(
        "Retrieval started - top_k: %d, filters: (chain=%s, risk=%s, mitre=%s)",
        top_k,
        filter_chain_id,
        filter_risk,
        filter_mitre,
    )

    if not question:
        logger.warning("Empty question received in retrieve_node")
        state["retrieved_documents"] = []
        return state

    # Retrieve via provided service instance or singleton
    qdrant_service: QdrantService = state.get("_qdrant_service") or QdrantService.get_instance()

    try:
        docs = qdrant_service.search(
            query=question,
            top_k=top_k,
            filter_chain_id=filter_chain_id,
            filter_risk=filter_risk,
            filter_mitre=filter_mitre,
        )
        logger.info("Documents retrieved: %d (in %.3fs)", len(docs), time.time() - start_time)
        state["retrieved_documents"] = [d.model_dump() if hasattr(d, "model_dump") else d for d in docs]
    except Exception as e:
        logger.error("Error during Qdrant vector retrieval: %s", str(e), exc_info=True)
        state["retrieved_documents"] = []

    return state
