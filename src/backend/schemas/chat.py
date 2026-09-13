"""
Pydantic V2 schemas for AI Analyst Chat System.
Covers chat queries, session management, chat history, and retrieved document structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    """Incoming user chat query with session identifier and optional RAG filters."""
    session_id: str = Field(..., description="Unique chat session UUID")
    question: str = Field(..., min_length=1, max_length=2000, description="Analyst question or query")
    filter_chain_id: Optional[str] = Field(None, description="Optional filter by attack chain ID (e.g. AC001)")
    filter_risk: Optional[str] = Field(None, description="Optional filter by risk level (Critical, High, Medium, Low)")
    filter_mitre: Optional[str] = Field(None, description="Optional filter by MITRE technique (e.g. T1110)")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of threat intelligence documents to retrieve")


class ThreatDocSchema(BaseModel):
    """Structured format for threat intelligence documents stored in and retrieved from Qdrant."""
    chain_id: str = Field(..., description="Attack Chain ID (e.g. AC001)")
    risk: str = Field(..., description="Risk Level (Critical, High, Medium, Low)")
    summary: str = Field(..., description="Summary of attack chain, report, or recommendations")
    mitre: List[str] = Field(default_factory=list, description="Associated MITRE ATT&CK technique IDs")
    doc_type: str = Field(default="threat_analysis", description="Document type: attack_chain, bluf_report, recommendation, mitre_summary")
    score: Optional[float] = Field(None, description="Vector similarity search score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")


class ChatResponse(BaseModel):
    """Analyst response grounded strictly in retrieved threat intelligence data."""
    answer: str = Field(..., description="Concise, explainable senior threat analyst response")
    session_id: str = Field(..., description="Chat session UUID")
    retrieved_documents: List[ThreatDocSchema] = Field(
        default_factory=list,
        description="Retrieved intelligence documents used for grounding"
    )
    execution_time_seconds: Optional[float] = Field(None, description="End-to-end response generation time")


class NewSessionResponse(BaseModel):
    """Response returned when initiating a fresh analyst chat session."""
    session_id: str = Field(..., description="Newly generated UUID for the chat session")


class ChatMessage(BaseModel):
    """A single conversation turn in chat history."""
    id: UUID
    session_id: UUID
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    message: str = Field(..., description="Message text content")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """Full chat history response for a session."""
    session_id: str
    total_messages: int
    history: List[ChatMessage]
