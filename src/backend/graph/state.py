"""
LangGraph state definition for the Threat Intelligence Correlation & Alert Prioritisation Workflow.
"""

from typing import Any, Dict, List, Optional, TypedDict


class ThreatWorkflowState(TypedDict, total=False):
    """
    Typed state dictionary passed through every node in the LangGraph workflow.
    Guarantees consistent schema, auditable progression, and state recovery.
    """
    chain_id: str
    attack_chain: Optional[Dict[str, Any]]
    behavioral_analysis: Optional[Dict[str, Any]]
    mitre_mappings: Optional[List[Dict[str, Any]]]
    risk_score: Optional[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    status: str                         # "pending" | "in_progress" | "completed" | "failed"
    errors: List[str]
    timestamp: str
    execution_metadata: Optional[Dict[str, Any]]
    _db: Optional[Any]                  # Active SQLAlchemy Session reference
    _user_id: Optional[Any]             # Scoped tenant/user UUID


class ChatState(TypedDict, total=False):
    """
    ChatState for AI Analyst Chat System.
    """
    question: str
    retrieved_documents: List[Dict[str, Any]]
    answer: str
    chat_history: List[Dict[str, Any]]
    timestamp: str
    session_id: Optional[str]
    filter_chain_id: Optional[str]
    filter_risk: Optional[str]
    filter_mitre: Optional[str]
    top_k: Optional[int]
    user_id: Optional[Any]
    _db: Optional[Any]
    _qdrant_service: Optional[Any]

