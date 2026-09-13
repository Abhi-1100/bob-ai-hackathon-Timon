"""
LangGraph Workflow Orchestrator for the AI Analyst Chat System.
Flow: START -> retrieve_node -> answer_node -> memory_node -> END.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

try:
    from nodes.retrieve_node import retrieve_node
    from nodes.answer_node import answer_node
    from nodes.memory_node import memory_node
except ImportError:
    from backend.nodes.retrieve_node import retrieve_node
    from backend.nodes.answer_node import answer_node
    from backend.nodes.memory_node import memory_node

logger = logging.getLogger("threat_intelligence.graph.analyst")


class ChatState(TypedDict, total=False):
    """
    ChatState as defined for the AI Analyst Chat System.
    Required Fields:
      question
      retrieved_documents
      answer
      chat_history
      timestamp
    """
    question: str
    retrieved_documents: List[Dict[str, Any]]
    answer: str
    chat_history: List[Dict[str, Any]]
    timestamp: str
    # Contextual runtime fields
    session_id: Optional[str]
    filter_chain_id: Optional[str]
    filter_risk: Optional[str]
    filter_mitre: Optional[str]
    top_k: Optional[int]
    _db: Optional[Any]
    _qdrant_service: Optional[Any]


def build_analyst_graph():
    """
    Constructs and compiles the LangGraph StateGraph workflow:
    START -> retrieve_node -> answer_node -> memory_node -> END.
    """
    workflow = StateGraph(ChatState)

    workflow.add_node("retrieve_node", retrieve_node)
    workflow.add_node("answer_node", answer_node)
    workflow.add_node("memory_node", memory_node)

    workflow.add_edge(START, "retrieve_node")
    workflow.add_edge("retrieve_node", "answer_node")
    workflow.add_edge("answer_node", "memory_node")
    workflow.add_edge("memory_node", END)

    app = workflow.compile()
    return app


# Singleton compiled graph app
analyst_graph_app = build_analyst_graph()
