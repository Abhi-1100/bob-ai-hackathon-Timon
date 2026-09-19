"""
SQLAlchemy ORM models for the Threat Intelligence Correlation & Alert Prioritisation Assistant.
Includes `Upload`, `Alert`, `AttackChainDB`, and `AttackChainEventDB` tables
with UUID primary keys, timestamps, indexes, and relationships.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Helper to use PostgreSQL UUID when available, otherwise fallback to String
def UUIDColumn():
    return Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
class Upload(Base):
    __tablename__ = "uploads"

    id = UUIDColumn()
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("UserDB", lazy="joined")
    alerts = relationship(
        "Alert",
        back_populates="upload",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_uploads_user_id", "user_id"),
        Index("ix_uploads_file_name", "file_name"),
        Index("ix_uploads_uploaded_at", "uploaded_at"),
    )

    def __repr__(self) -> str:
        return f"<Upload id={self.id} user_id={self.user_id} file_name={self.file_name}>"


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------
class Alert(Base):
    __tablename__ = "alerts"

    id = UUIDColumn()
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    upload_id = Column(PG_UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    src_ip = Column(String(100), nullable=False)
    dst_ip = Column(String(100), nullable=False)
    event = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to upload
    upload = relationship("Upload", back_populates="alerts", lazy="joined")

    # Relationship to attack chain events (many-to-many via junction table)
    chain_events = relationship("AttackChainEventDB", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_alerts_user_id", "user_id"),
        Index("ix_alerts_src_ip", "src_ip"),
        Index("ix_alerts_dst_ip", "dst_ip"),
        Index("ix_alerts_timestamp", "timestamp"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_event", "event"),
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} upload_id={self.upload_id} "
            f"event={self.event} severity={self.severity}>"
        )


# ---------------------------------------------------------------------------
# Attack Chain
# ---------------------------------------------------------------------------
class AttackChainDB(Base):
    """Stores correlated attack chains produced by the rule-based correlation engine."""
    __tablename__ = "attack_chains"

    id = UUIDColumn()
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    chain_id = Column(String(50), nullable=False)
    source_ip = Column(String(100), nullable=False)
    destination_ips = Column(Text, nullable=True)       # Comma-separated list
    events = Column(Text, nullable=True)                # Comma-separated event progression
    alert_count = Column(Integer, nullable=False, default=0)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to junction table
    chain_events = relationship(
        "AttackChainEventDB",
        back_populates="chain",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship to MITRE mappings
    mitre_mappings = relationship(
        "MitreMappingDB",
        back_populates="attack_chain",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship to risk score (one-to-one)
    risk_score = relationship(
        "RiskScoreDB",
        back_populates="attack_chain",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship to recommendation (one-to-one)
    recommendation = relationship(
        "RecommendationDB",
        back_populates="attack_chain",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship to executive report (one-to-one)
    report = relationship(
        "ReportDB",
        back_populates="attack_chain",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship to behavioral analysis (one-to-one)
    behavioral_analysis = relationship(
        "BehavioralAnalysisDB",
        back_populates="attack_chain",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_attack_chains_user_id", "user_id"),
        Index("ix_attack_chains_user_chain", "user_id", "chain_id", unique=True),
        Index("ix_attack_chains_chain_id", "chain_id"),
        Index("ix_attack_chains_source_ip", "source_ip"),
        Index("ix_attack_chains_start_time", "start_time"),
    )

    def __repr__(self) -> str:
        return f"<AttackChainDB user_id={self.user_id} chain_id={self.chain_id} source_ip={self.source_ip} alerts={self.alert_count}>"


# ---------------------------------------------------------------------------
# Attack Chain Events (junction / many-to-many)
# ---------------------------------------------------------------------------
class AttackChainEventDB(Base):
    """Junction table linking alerts to attack chains (many-to-many)."""
    __tablename__ = "attack_chain_events"

    id = UUIDColumn()
    chain_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("attack_chains.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    chain = relationship("AttackChainDB", back_populates="chain_events")
    alert = relationship("Alert", back_populates="chain_events")

    __table_args__ = (
        Index("ix_chain_events_chain_id", "chain_id"),
        Index("ix_chain_events_alert_id", "alert_id"),
    )

    def __repr__(self) -> str:
        return f"<AttackChainEventDB chain_id={self.chain_id} alert_id={self.alert_id}>"


# ---------------------------------------------------------------------------
# MITRE ATT&CK Mappings
# ---------------------------------------------------------------------------
class MitreMappingDB(Base):
    """Stores MITRE ATT&CK technique mappings for attack chains."""
    __tablename__ = "mitre_mappings"

    id = UUIDColumn()
    attack_chain_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("attack_chains.id", ondelete="CASCADE"),
        nullable=False,
    )
    technique_id = Column(String(50), nullable=False)
    technique_name = Column(String(255), nullable=False)
    tactic = Column(String(100), nullable=True, default="Unknown")
    event = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to attack chain
    attack_chain = relationship("AttackChainDB", back_populates="mitre_mappings")

    __table_args__ = (
        Index("ix_mitre_mappings_chain_id", "attack_chain_id"),
        Index("ix_mitre_mappings_technique_id", "technique_id"),
    )

    def __repr__(self) -> str:
        return f"<MitreMappingDB technique_id={self.technique_id} name={self.technique_name}>"


# ---------------------------------------------------------------------------
# Risk Scores
# ---------------------------------------------------------------------------
class RiskScoreDB(Base):
    """Stores calculated risk scores for attack chains."""
    __tablename__ = "risk_scores"

    id = UUIDColumn()
    attack_chain_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("attack_chains.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    score = Column(Integer, nullable=False, default=0)
    level = Column(String(50), nullable=False, default="Low")
    reasoning = Column(Text, nullable=True)  # JSON-encoded list of strings
    event_score = Column(Integer, nullable=False, default=0)
    mitre_score = Column(Integer, nullable=False, default=0)
    chain_bonus = Column(Integer, nullable=False, default=0)
    behavioral_score = Column(Integer, nullable=True)
    behavioral_level = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to attack chain
    attack_chain = relationship("AttackChainDB", back_populates="risk_score")

    __table_args__ = (
        Index("ix_risk_scores_chain_id", "attack_chain_id"),
        Index("ix_risk_scores_level", "level"),
        Index("ix_risk_scores_score", "score"),
    )

    def __repr__(self) -> str:
        return f"<RiskScoreDB score={self.score} level={self.level}>"


# ---------------------------------------------------------------------------
# LLM Security Recommendations
# ---------------------------------------------------------------------------
class RecommendationDB(Base):
    """Stores LLM-generated actionable security recommendations for attack chains."""
    __tablename__ = "recommendations"

    id = UUIDColumn()
    attack_chain_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("attack_chains.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    immediate_actions = Column(Text, nullable=False)        # JSON list
    containment_actions = Column(Text, nullable=False)      # JSON list
    investigation_actions = Column(Text, nullable=False)    # JSON list
    prevention_actions = Column(Text, nullable=False)       # JSON list
    executive_summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to attack chain
    attack_chain = relationship("AttackChainDB", back_populates="recommendation")

    __table_args__ = (
        Index("ix_recommendations_chain_id", "attack_chain_id"),
        Index("ix_recommendations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RecommendationDB id={self.id} attack_chain_id={self.attack_chain_id}>"


# ---------------------------------------------------------------------------
# Executive BLUF Reports
# ---------------------------------------------------------------------------
class ReportDB(Base):
    """Stores generated executive BLUF threat intelligence reports."""
    __tablename__ = "reports"

    id = UUIDColumn()
    attack_chain_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("attack_chains.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    threat_level = Column(String(50), nullable=False)
    executive_summary = Column(Text, nullable=False)
    attack_overview = Column(Text, nullable=False)
    affected_assets = Column(Text, nullable=False)
    mitre_summary = Column(Text, nullable=False)
    risk_assessment = Column(Text, nullable=False)
    recommended_actions = Column(Text, nullable=False)
    conclusion = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to attack chain
    attack_chain = relationship("AttackChainDB", back_populates="report")

    __table_args__ = (
        Index("ix_reports_chain_id", "attack_chain_id"),
        Index("ix_reports_threat_level", "threat_level"),
        Index("ix_reports_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReportDB id={self.id} threat_level={self.threat_level}>"


# ---------------------------------------------------------------------------
# Chat History
# ---------------------------------------------------------------------------
class ChatHistoryDB(Base):
    """Stores conversation turns for the AI Analyst Chat System."""
    __tablename__ = "chat_history"

    id = UUIDColumn()
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(PG_UUID(as_uuid=True), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_chat_history_user_id", "user_id"),
        Index("ix_chat_history_session_id", "session_id"),
        Index("ix_chat_history_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatHistoryDB id={self.id} user_id={self.user_id} session_id={self.session_id} role={self.role}>"


# ---------------------------------------------------------------------------
# User (Enterprise Authentication)
# ---------------------------------------------------------------------------
class UserDB(Base):
    """Stores operator and analyst accounts for authentication."""
    __tablename__ = "users"

    id = UUIDColumn()
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=False)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<UserDB id={self.id} email={self.email}>"


# ---------------------------------------------------------------------------
# Behavioral + Context Analysis
# ---------------------------------------------------------------------------
class EntityBaselineDB(Base):
    """Stores behavioral baselines per entity for anomaly detection."""
    __tablename__ = "entity_baselines"

    id = UUIDColumn()
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    entity_type = Column(String(50), nullable=False) # e.g. 'ip', 'user', 'device'
    entity_value = Column(String(255), nullable=False)
    observation_count = Column(Integer, nullable=False, default=0)
    avg_events_per_hour = Column(Integer, nullable=False, default=0) # Storing as scaled integer or use Float
    peak_events_per_hour = Column(Integer, nullable=False, default=0)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_entity_baselines_user_id", "user_id"),
        Index("ix_entity_baselines_type_value", "entity_type", "entity_value"),
    )

    def __repr__(self) -> str:
        return f"<EntityBaselineDB type={self.entity_type} value={self.entity_value}>"


class BehavioralAnalysisDB(Base):
    """Stores the full behavioral analysis result per attack chain."""
    __tablename__ = "behavioral_analyses"

    id = UUIDColumn()
    attack_chain_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("attack_chains.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    anomaly_score = Column(Integer, nullable=False, default=0)
    anomaly_level = Column(String(50), nullable=False)
    signals = Column(Text, nullable=True) # JSON list
    dimension_breakdown = Column(Text, nullable=True) # JSON dict
    why_prioritized = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to attack chain
    attack_chain = relationship("AttackChainDB", back_populates="behavioral_analysis")

    __table_args__ = (
        Index("ix_behavioral_analyses_chain_id", "attack_chain_id"),
        Index("ix_behavioral_analyses_level", "anomaly_level"),
    )

    def __repr__(self) -> str:
        return f"<BehavioralAnalysisDB score={self.anomaly_score} level={self.anomaly_level}>"



