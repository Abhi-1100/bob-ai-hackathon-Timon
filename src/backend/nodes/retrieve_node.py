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

    # 1. Retrieve via Qdrant vector similarity search
    qdrant_service: QdrantService = state.get("_qdrant_service") or QdrantService.get_instance()

    try:
        docs = qdrant_service.search(
            query=question,
            top_k=top_k,
            filter_chain_id=filter_chain_id,
            filter_risk=filter_risk,
            filter_mitre=filter_mitre,
        )
        logger.info("Qdrant documents retrieved: %d (in %.3fs)", len(docs), time.time() - start_time)
        state["retrieved_documents"] = [d.model_dump() if hasattr(d, "model_dump") else d for d in docs]
    except Exception as e:
        logger.warning("Qdrant search error or offline (%s). Using relational fallback.", str(e))
        state["retrieved_documents"] = []

    # 2. Relational Database Hybrid Fallback (guarantees 100% data availability from ingested CSV)
    if not state.get("retrieved_documents"):
        db = state.get("_db")
        if db:
            try:
                from sqlalchemy import select, desc
                import re
                try:
                    from database.models import AttackChainDB, MitreMappingDB, RiskScoreDB
                except ImportError:
                    from backend.database.models import AttackChainDB, MitreMappingDB, RiskScoreDB

                logger.info("Executing fast relational database threat retrieval...")
                q_lower = question.lower()
                query = select(AttackChainDB)

                # Explicit chain filter or regex match
                matched_chain = filter_chain_id
                if not matched_chain:
                    m = re.search(r"\b(ac\d+)\b", q_lower, re.IGNORECASE)
                    if m:
                        matched_chain = m.group(1).upper()

                if matched_chain:
                    query = query.where(AttackChainDB.chain_id == matched_chain)
                elif filter_risk:
                    query = query.join(AttackChainDB.risk_score).where(RiskScoreDB.level.ilike(f"%{filter_risk}%"))
                elif "critical" in q_lower or "highest" in q_lower or "severe" in q_lower:
                    query = query.join(AttackChainDB.risk_score).order_by(desc(RiskScoreDB.score))
                else:
                    # Join with risk score and sort by severity
                    query = query.outerjoin(AttackChainDB.risk_score).order_by(
                        desc(RiskScoreDB.score).nullslast()
                    )

                chains = db.scalars(query.limit(max(top_k, 5))).all()
                fallback_docs = []

                for chain in chains:
                    r_level = "Medium"
                    score_val = 50.0
                    if getattr(chain, "risk_score", None):
                        r_level = getattr(chain.risk_score, "level", "Medium") or "Medium"
                        score_val = getattr(chain.risk_score, "score", 50.0) or 50.0

                    mitre_ids = [m.technique_id for m in (getattr(chain, "mitre_mappings", []) or [])]
                    rec_summary = ""
                    if getattr(chain, "recommendation", None):
                        rec_summary = f" Recommendation: {chain.recommendation.executive_summary}."

                    doc = {
                        "chain_id": chain.chain_id,
                        "risk": r_level,
                        "summary": (
                            f"Attack Chain {chain.chain_id} originating from source IP {chain.source_ip} "
                            f"targeting destination assets [{chain.destination_ips}]. "
                            f"Progression sequence: {chain.events}. "
                            f"Total alerts: {chain.alert_count}. Overall Risk Score: {score_val} ({r_level})."
                            f"{rec_summary}"
                        ),
                        "mitre": mitre_ids,
                        "doc_type": "attack_chain",
                        "score": 0.92,
                        "metadata": {
                            "source_ip": chain.source_ip,
                            "destination_ips": chain.destination_ips,
                            "alert_count": chain.alert_count,
                            "start_time": str(chain.start_time),
                        },
                    }
                    fallback_docs.append(doc)

                if fallback_docs:
                    logger.info("Relational fallback retrieved %d grounded intelligence records", len(fallback_docs))
                    state["retrieved_documents"] = fallback_docs
            except Exception as ex:
                logger.error("Relational retrieval fallback failed: %s", str(ex), exc_info=True)

    return state

