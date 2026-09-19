"""
Qdrant Vector Database Service for Threat Intelligence Document Storage and RAG Retrieval.
Utilizes BAAI/bge-small-en-v1.5 embeddings via FastEmbed (384-dimensional dense vectors).
"""

import os
import uuid
import logging
from typing import Any, Dict, List, Optional
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from fastembed import TextEmbedding
try:
    from schemas.chat import ThreatDocSchema
except ImportError:
    from backend.schemas.chat import ThreatDocSchema

logger = logging.getLogger("threat_intelligence.qdrant")

COLLECTION_NAME = "threat_intelligence"
VECTOR_SIZE = 384  # BAAI/bge-small-en-v1.5 vector dimensionality


class QdrantService:
    """Manages Qdrant vector index lifecycle, embedding caching, and metadata-filtered search."""

    _instance: Optional["QdrantService"] = None

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = COLLECTION_NAME,
        in_memory: bool = False,
    ):
        self.collection_name = collection_name
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")

        # Initialize client (in-memory or network client)
        if in_memory or not self.url:
            logger.info("Initializing in-memory Qdrant client")
            self.client = QdrantClient(":memory:")
        else:
            logger.info("Connecting to remote Qdrant at %s", self.url)
            self.client = QdrantClient(url=self.url, api_key=self.api_key)

        # Initialize FastEmbed embedding model (singleton / cached)
        self._embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self._embed_cache: Dict[str, List[float]] = {}

        self._ensure_collection()

    @classmethod
    def get_instance(cls) -> "QdrantService":
        """Singleton accessor for Qdrant service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_collection(self) -> None:
        """Create threat_intelligence collection with Cosine similarity if missing."""
        try:
            collections = self.client.get_collections().collections
            existing_names = [c.name for c in collections]
            if self.collection_name not in existing_names:
                logger.info("Creating Qdrant collection '%s'", self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=VECTOR_SIZE,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
            # Ensure payload indices exist for filtered query fields
            for field in ["user_id", "chain_id", "risk", "mitre"]:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=qmodels.PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass
        except Exception as e:
            # Qdrant is an enrichment dependency; deterministic ingestion and
            # the API must remain available when the remote vector service is
            # temporarily unreachable (including offline test environments).
            logger.warning(
                "Failed to reach Qdrant collection '%s': %s; falling back to in-memory Qdrant",
                self.collection_name,
                str(e),
            )
            self.client = QdrantClient(":memory:")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE),
            )

    def get_embedding(self, text: str) -> List[float]:
        """Compute 384-dimensional embedding for given text with in-memory caching."""
        clean_text = text.strip()
        if clean_text in self._embed_cache:
            return self._embed_cache[clean_text]

        embeddings = list(self._embedder.embed([clean_text]))
        vector = embeddings[0].tolist()
        # Cap cache to 5000 items
        if len(self._embed_cache) < 5000:
            self._embed_cache[clean_text] = vector
        return vector

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Batch compute embeddings for multiple texts."""
        clean_texts = [t.strip() for t in texts]
        results: List[List[float]] = []
        to_compute_indices = []
        to_compute_texts = []

        for i, text in enumerate(clean_texts):
            if text in self._embed_cache:
                results.append(self._embed_cache[text])
            else:
                results.append([])
                to_compute_indices.append(i)
                to_compute_texts.append(text)

        if to_compute_texts:
            computed = list(self._embedder.embed(to_compute_texts))
            for idx, comp in zip(to_compute_indices, computed):
                vec = comp.tolist()
                results[idx] = vec
                if len(self._embed_cache) < 5000:
                    self._embed_cache[clean_texts[idx]] = vec

        return results

    def upsert_document(self, doc: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Upsert a single threat intelligence document into Qdrant.
        Required payload fields: chain_id, risk, summary, mitre (list).
        Optional tenant field: user_id.
        """
        point_id = doc_id or str(uuid.uuid4())
        summary_text = doc.get("summary", "")
        chain_id = doc.get("chain_id", "UNKNOWN")
        risk = doc.get("risk", "Medium")
        mitre = doc.get("mitre", [])
        doc_type = doc.get("doc_type", "threat_analysis")
        user_id = doc.get("user_id")

        # Rich text representation for embedding semantic richness
        embed_input = f"Attack Chain: {chain_id}. Risk: {risk}. MITRE: {', '.join(mitre)}. Summary: {summary_text}"
        vector = self.get_embedding(embed_input)

        payload = {
            "chain_id": chain_id,
            "risk": risk,
            "summary": summary_text,
            "mitre": mitre,
            "doc_type": doc_type,
            "user_id": str(user_id) if user_id is not None else None,
            "metadata": doc.get("metadata", {}),
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        return point_id

    def upsert_documents(self, docs: List[Dict[str, Any]]) -> int:
        """Batch upsert multiple threat intelligence documents."""
        if not docs:
            return 0

        embed_texts = []
        for doc in docs:
            chain_id = doc.get("chain_id", "UNKNOWN")
            risk = doc.get("risk", "Medium")
            mitre = doc.get("mitre", [])
            summary = doc.get("summary", "")
            embed_texts.append(f"Attack Chain: {chain_id}. Risk: {risk}. MITRE: {', '.join(mitre)}. Summary: {summary}")

        vectors = self.get_embeddings(embed_texts)
        points = []
        for i, (doc, vector) in enumerate(zip(docs, vectors)):
            point_id = doc.get("doc_id") or str(uuid.uuid4())
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "chain_id": doc.get("chain_id", "UNKNOWN"),
                        "risk": doc.get("risk", "Medium"),
                        "summary": doc.get("summary", ""),
                        "mitre": doc.get("mitre", []),
                        "doc_type": doc.get("doc_type", "threat_analysis"),
                        "user_id": str(doc.get("user_id")) if doc.get("user_id") is not None else None,
                        "metadata": doc.get("metadata", {}),
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return len(points)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_chain_id: Optional[str] = None,
        filter_risk: Optional[str] = None,
        filter_mitre: Optional[str] = None,
        filter_user_id: Optional[Any] = None,
    ) -> List[ThreatDocSchema]:
        """
        Execute vector similarity search with optional Qdrant metadata filters.
        Filters supported: risk level, chain id, MITRE technique, user_id (tenant isolation).
        """
        query_vector = self.get_embedding(query)

        filter_conditions = []
        if filter_chain_id:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="chain_id",
                    match=qmodels.MatchValue(value=filter_chain_id.strip()),
                )
            )
        if filter_risk:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="risk",
                    match=qmodels.MatchValue(value=filter_risk.strip()),
                )
            )
        if filter_mitre:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="mitre",
                    match=qmodels.MatchValue(value=filter_mitre.strip().upper()),
                )
            )
        if filter_user_id is not None:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=str(filter_user_id)),
                )
            )

        query_filter = None
        if filter_conditions:
            query_filter = qmodels.Filter(must=filter_conditions)

        # Query points using query_points (recommended in qdrant-client >= 1.7)
        try:
            search_response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
            hits = search_response.points
        except AttributeError:
            # Fallback for older client APIs
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
            )

        results: List[ThreatDocSchema] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                ThreatDocSchema(
                    chain_id=payload.get("chain_id", "UNKNOWN"),
                    risk=payload.get("risk", "Medium"),
                    summary=payload.get("summary", ""),
                    mitre=payload.get("mitre", []),
                    doc_type=payload.get("doc_type", "threat_analysis"),
                    score=hit.score if hasattr(hit, "score") else None,
                    user_id=payload.get("user_id"),
                    metadata=payload.get("metadata", {}),
                )
            )

        return results

    def sync_from_database(self, db, user_id: Optional[Any] = None) -> int:
        """
        Harvest all correlated attack chains, MITRE mappings, risk scores,
        recommendations, and BLUF reports from relational DB into Qdrant.
        Optionally filter by user_id for strict multi-tenant isolation.
        """
        import json
        from sqlalchemy import select
        try:
            from database.models import (
                AttackChainDB,
                MitreMappingDB,
                RiskScoreDB,
                RecommendationDB,
                ReportDB,
            )
        except ImportError:
            from backend.database.models import (
                AttackChainDB,
                MitreMappingDB,
                RiskScoreDB,
                RecommendationDB,
                ReportDB,
            )

        docs_to_index: List[Dict[str, Any]] = []

        # 1. Fetch attack chains with related data (filtered by user_id if provided)
        stmt = select(AttackChainDB)
        if user_id is not None:
            stmt = stmt.where(AttackChainDB.user_id == user_id)
        # Order by alert_count desc to index highest-priority chains first
        stmt = stmt.order_by(AttackChainDB.alert_count.desc()).limit(50)
        chains = db.scalars(stmt).all()

        for chain in chains:
            # Gather associated MITRE techniques from preloaded relationship
            mitre_mappings = getattr(chain, "mitre_mappings", None) or []
            mitre_ids = [m.technique_id for m in mitre_mappings]

            # Gather risk score from preloaded relationship
            risk_score = getattr(chain, "risk_score", None)
            risk_level = (
                getattr(risk_score, "level", None)
                or getattr(risk_score, "severity", None)
                or "Medium"
            )
            score_num = (
                getattr(risk_score, "score", None)
                or getattr(risk_score, "overall_score", None)
                or 50.0
            )

            # Gather behavioral context from preloaded relationship
            ba = getattr(chain, "behavioral_analysis", None)
            ba_text = ""
            if ba:
                ba_text = f" Behavioral Anomaly Score: {ba.anomaly_score}/100 ({ba.anomaly_level}). Prioritization: {ba.why_prioritized}."

            # Chain document with user_id tenant identifier
            chain_doc = {
                "chain_id": chain.chain_id,
                "risk": risk_level,
                "summary": (
                    f"Attack Chain {chain.chain_id} originating from source IP {chain.source_ip} "
                    f"targeting destinations [{chain.destination_ips}]. "
                    f"Progression sequence: {chain.events}. "
                    f"Total alerts: {chain.alert_count}. Overall Risk Score: {score_num} ({risk_level})."
                    f"{ba_text}"
                ),
                "mitre": mitre_ids,
                "doc_type": "attack_chain",
                "user_id": str(chain.user_id) if chain.user_id is not None else None,
                "metadata": {
                    "source_ip": chain.source_ip,
                    "alert_count": chain.alert_count,
                    "start_time": str(chain.start_time),
                    "end_time": str(chain.end_time),
                    "behavioral_score": ba.anomaly_score if ba else None,
                    "behavioral_level": ba.anomaly_level if ba else None,
                },
            }
            docs_to_index.append(chain_doc)

            # 1b. Check Contextual Behavioral Analysis doc
            if ba:
                ba_signals = []
                if ba.signals:
                    try:
                        sig_data = json.loads(ba.signals) if isinstance(ba.signals, str) else ba.signals
                        ba_signals = [s.get("description", "") for s in sig_data if isinstance(s, dict)]
                    except Exception:
                        pass
                ba_doc = {
                    "chain_id": chain.chain_id,
                    "risk": risk_level,
                    "summary": (
                        f"Contextual Behavioral Anomaly Analysis for Attack Chain {chain.chain_id}: "
                        f"Anomaly Score: {ba.anomaly_score}/100 ({ba.anomaly_level}). "
                        f"Rationale: {ba.why_prioritized or 'Standard context signals'}. "
                        f"Observed Behavioral Signals: {'; '.join(ba_signals[:5])}."
                    ),
                    "mitre": mitre_ids,
                    "doc_type": "behavioral_analysis",
                    "user_id": str(chain.user_id) if chain.user_id is not None else None,
                    "metadata": {
                        "anomaly_score": ba.anomaly_score,
                        "anomaly_level": ba.anomaly_level,
                    },
                }
                docs_to_index.append(ba_doc)

            # 2. Check Recommendations from preloaded relationship
            rec = getattr(chain, "recommendation", None)
            if rec:
                def _parse_actions(field_val):
                    if not field_val:
                        return []
                    if isinstance(field_val, list):
                        return field_val
                    try:
                        parsed = json.loads(field_val)
                        if isinstance(parsed, list):
                            return parsed
                        return [str(parsed)]
                    except Exception:
                        return [str(field_val)]

                imm_list = _parse_actions(getattr(rec, "immediate_actions", None) or getattr(rec, "immediate_containment", None))
                cont_list = _parse_actions(getattr(rec, "containment_actions", None))
                inv_list = _parse_actions(getattr(rec, "investigation_actions", None) or getattr(rec, "system_remediation", None))
                prev_list = _parse_actions(getattr(rec, "prevention_actions", None))

                combined_actions = imm_list + cont_list + inv_list

                rec_doc = {
                    "chain_id": chain.chain_id,
                    "risk": risk_level,
                    "summary": (
                        f"Security Recommendations for Attack Chain {chain.chain_id}: "
                        f"Executive Summary: {rec.executive_summary}. "
                        f"Immediate and Containment Actions: {'; '.join(combined_actions[:4])}. "
                        f"Long-term Prevention: {'; '.join(prev_list[:4])}."
                    ),
                    "mitre": mitre_ids,
                    "doc_type": "recommendation",
                    "user_id": str(chain.user_id) if chain.user_id is not None else None,
                    "metadata": {"priority": getattr(rec, "priority", "High")},
                }
                docs_to_index.append(rec_doc)

            # 3. Check Executive BLUF Report from preloaded relationship
            report = getattr(chain, "report", None)
            if report:
                report_doc = {
                    "chain_id": chain.chain_id,
                    "risk": report.threat_level,
                    "summary": (
                        f"Executive BLUF Threat Report for Attack Chain {chain.chain_id}: "
                        f"Threat Level: {report.threat_level}. "
                        f"Executive Summary: {report.executive_summary}. "
                        f"Attack Overview: {report.attack_overview}. "
                        f"Conclusion: {report.conclusion}"
                    ),
                    "mitre": mitre_ids,
                    "doc_type": "bluf_report",
                    "user_id": str(chain.user_id) if chain.user_id is not None else None,
                    "metadata": {"threat_level": report.threat_level},
                }
                docs_to_index.append(report_doc)

        if not docs_to_index:
            logger.info("No threat intelligence documents found to sync into Qdrant.")
            return 0

        logger.info(f"Syncing {len(docs_to_index)} threat documents into Qdrant collection '{self.collection_name}'...")
        count = self.upsert_documents(docs_to_index)
        logger.info(f"Successfully synced {count} threat documents into Qdrant.")
        return count
