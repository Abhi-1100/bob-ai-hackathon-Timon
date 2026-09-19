"""
Behavioral and Context Analysis Layer.
Evaluates security events using general dimensions: Identity, Device, Network,
Target, Behavior, Time, History/Baseline, Relationships, and Impact.

This produces an explainable, contextual anomaly score (0-100)
without automatically assuming unknown = malicious.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import UUID

import json
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from database.models import AttackChainDB, Alert as AlertDB, BehavioralAnalysisDB
    from schemas.behavioral import DimensionSignal, BehavioralAnalysisResult
except ImportError:
    # Fallback for relative imports during testing
    from backend.database.models import AttackChainDB, Alert as AlertDB, BehavioralAnalysisDB
    from backend.schemas.behavioral import DimensionSignal, BehavioralAnalysisResult

logger = logging.getLogger("behavioral_analysis")

# ---------------------------------------------------------------------------
# Scoring Weights
# ---------------------------------------------------------------------------
BEHAVIOR_WEIGHTS: Dict[str, float] = {
    "identity": 0.10,
    "device": 0.12,
    "network": 0.12,
    "target": 0.15,
    "behavior": 0.18,
    "time": 0.08,
    "history": 0.15,
    "relationship": 0.10,
}

# Ensure weights sum to 1.0 (or very close to it)
_total_weight = sum(BEHAVIOR_WEIGHTS.values())
if abs(_total_weight - 1.0) > 0.01:
    logger.warning(f"BEHAVIOR_WEIGHTS sum to {_total_weight}, expected 1.0")


class BehaviorFeatureExtractor:
    """Extracts dimensional features from raw alerts and attack chains."""

    @staticmethod
    def extract_features(chain: AttackChainDB, alerts: List[AlertDB]) -> Dict[str, Any]:
        """
        Extract relevant telemetry from the chain's alerts.
        In a real system, this would parse user agents, active directory context, etc.
        from alert metadata. For this implementation, we infer basic features.
        """
        features: Dict[str, Any] = {
            "source_ip": chain.source_ip,
            "destination_ips": [ip.strip() for ip in (chain.destination_ips or "").split(",") if ip.strip()],
            "events": [e.strip() for e in (chain.events or "").split(",") if e.strip()],
            "start_time": chain.start_time,
            "end_time": chain.end_time,
            "alert_count": chain.alert_count,
            "metadata_list": [],
        }

        # Extract metadata from individual alerts if available (e.g. usernames, device IDs)
        # Note: AlertDB model in this project doesn't have a JSON metadata column directly
        # but in a full enterprise deployment, this is where it would be parsed.
        # We will simulate missing or inferred context based on available fields.

        # Infer basic timing features
        if chain.start_time:
            hour = chain.start_time.hour
            features["is_working_hours"] = 8 <= hour <= 18
            
        if chain.start_time and chain.end_time:
            duration = (chain.end_time - chain.start_time).total_seconds()
            features["duration_seconds"] = duration
            if duration > 0 and chain.alert_count > 1:
                features["velocity_alerts_per_second"] = chain.alert_count / duration
            elif chain.alert_count > 1:
                features["velocity_alerts_per_second"] = 999.0 # Burst
            else:
                features["velocity_alerts_per_second"] = 0.0

        return features


class BaselineService:
    """Manages historical baselines for entities to determine deviation."""

    def __init__(self, db: Session):
        self.db = db

    def get_baseline_context(self, user_id: Optional[UUID], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query historical baselines for the given features.
        Since we are just introducing this layer, if the baseline table is empty,
        we return defaults indicating 'first_seen'.
        """
        context: Dict[str, Any] = {
            "is_known_ip": False,  # We don't have historical data to prove otherwise yet
            "is_first_seen_ip": True,
            "is_known_target": False,
            "baseline_velocity": 0.0,
            "baseline_event_count_avg": 0.0,
        }
        
        # In a fully populated system, we would query the new EntityBaselineDB here
        # Example:
        # ip_baseline = self.db.query(EntityBaselineDB).filter(
        #     EntityBaselineDB.user_id == user_id, 
        #     EntityBaselineDB.entity_type == 'ip', 
        #     EntityBaselineDB.entity_value == features['source_ip']
        # ).first()
        # if ip_baseline:
        #     context["is_known_ip"] = True
        #     context["is_first_seen_ip"] = False
        
        return context


class AnomalyScorer:
    """Calculates the dimensional anomaly scores based on extracted features and baseline context."""

    @staticmethod
    def score_identity(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Identity dimension scoring."""
        # Simulated logic: if we had 'username' in features, we'd check if it's known
        # For now, we lack explicit identity context in the basic Alert model
        return DimensionSignal(
            dimension="identity",
            score=0.0,
            signals=[],
            available=False
        )

    @staticmethod
    def score_device(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Device dimension scoring."""
        # Simulated logic: if we had 'device_id' or 'user_agent'
        return DimensionSignal(
            dimension="device",
            score=0.0,
            signals=[],
            available=False
        )

    @staticmethod
    def score_network(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Network dimension scoring based on source IP."""
        score = 0.0
        signals = []
        
        src_ip = features.get("source_ip", "")
        
        # Basic heuristic: non-RFC1918 IPs might be external
        is_internal = src_ip.startswith("10.") or src_ip.startswith("192.168.") or (src_ip.startswith("172.") and 16 <= int(src_ip.split(".")[1]) <= 31)
        
        if not is_internal:
            signals.append("External source IP")
            score += 20.0
            
        if context.get("is_first_seen_ip"):
            signals.append("IP address observed for the first time")
            score += 30.0
            
        return DimensionSignal(
            dimension="network",
            score=min(100.0, score),
            signals=signals,
            available=True
        )

    @staticmethod
    def score_target(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Target/Resource dimension scoring based on destination IPs/assets."""
        score = 0.0
        signals = []
        
        dest_ips = features.get("destination_ips", [])
        if dest_ips:
            if not context.get("is_known_target"):
                signals.append("First-time access to target resource(s)")
                score += 40.0
                
            if len(dest_ips) > 3:
                signals.append(f"Multiple targets accessed ({len(dest_ips)})")
                score += 20.0
                
        return DimensionSignal(
            dimension="target",
            score=min(100.0, score),
            signals=signals,
            available=True
        )

    @staticmethod
    def score_behavior(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Behavioral dimension scoring based on event velocity and volume."""
        score = 0.0
        signals = []
        
        velocity = features.get("velocity_alerts_per_second", 0.0)
        events = features.get("events", [])
        
        if velocity > 10.0:
            signals.append("High-velocity burst activity")
            score += 60.0
        elif velocity > 2.0:
            signals.append("Elevated activity rate")
            score += 30.0
            
        unique_events = len(set(events))
        if unique_events > 3:
            signals.append("High diversity of security events")
            score += 20.0
            
        return DimensionSignal(
            dimension="behavior",
            score=min(100.0, score),
            signals=signals,
            available=True
        )

    @staticmethod
    def score_time(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Time dimension scoring based on when activity occurred."""
        score = 0.0
        signals = []
        
        if not features.get("is_working_hours", True):
            signals.append("Activity outside normal business hours")
            score += 30.0
            
        return DimensionSignal(
            dimension="time",
            score=min(100.0, score),
            signals=signals,
            available=True
        )

    @staticmethod
    def score_history(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """History/Baseline dimension scoring."""
        score = 0.0
        signals = []
        
        # If everything is first seen, deviation is technically high, but we shouldn't
        # heavily penalize a brand new environment.
        if context.get("is_first_seen_ip") and not context.get("is_known_target"):
            signals.append("No historical baseline exists for these entities")
            score += 20.0  # Mild anomaly for completely new behavior
            
        return DimensionSignal(
            dimension="history",
            score=min(100.0, score),
            signals=signals,
            available=True
        )

    @staticmethod
    def score_relationship(features: Dict[str, Any], context: Dict[str, Any]) -> DimensionSignal:
        """Relationship dimension scoring."""
        # Lacking explicit user/device context, we simulate this based on IP/Target
        score = 0.0
        signals = []
        
        if context.get("is_first_seen_ip") and not context.get("is_known_target"):
            signals.append("Novel source-to-target relationship")
            score += 30.0
            
        return DimensionSignal(
            dimension="relationship",
            score=min(100.0, score),
            signals=signals,
            available=True
        )

    @classmethod
    def calculate_total_anomaly(cls, dimensions: Dict[str, DimensionSignal]) -> Tuple[float, str, List[str], str]:
        """
        Combines dimensional scores using BEHAVIOR_WEIGHTS.
        Returns (total_score, level_label, top_signals, prioritization_reason)
        """
        total_score = 0.0
        all_signals = []
        
        for dim, signal in dimensions.items():
            if signal.available:
                weight = BEHAVIOR_WEIGHTS.get(dim, 0.0)
                total_score += signal.score * weight
                all_signals.extend(signal.signals)
                
        total_score = min(100.0, max(0.0, total_score))
        
        # Determine level
        if total_score >= 80:
            level = "Critical"
        elif total_score >= 60:
            level = "High"
        elif total_score >= 40:
            level = "Elevated"
        elif total_score >= 25:
            level = "Low"
        else:
            level = "Normal"
            
        # Select top signals (just taking first few for now, could be smarter)
        top_signals = all_signals[:5]
        
        # Generate generic explanation
        reason = "Behavioral analysis found normal patterns."
        if total_score >= 60:
            if "High-velocity burst activity" in all_signals:
                reason = "High velocity anomalous activity identified."
            elif "External source IP" in all_signals and "First-time access to target resource(s)" in all_signals:
                reason = "Novel external access to internal resources observed."
            else:
                reason = "Multiple anomalous behavioral signals combined to elevate priority."
        elif total_score >= 40:
            reason = "Some anomalous behavioral signals observed; warrants review."
            
        return total_score, level, top_signals, reason


class BehavioralAnalysisEngine:
    """Main orchestrator for behavioral analysis."""

    def __init__(self, db: Session):
        self.db = db
        self.extractor = BehaviorFeatureExtractor()
        self.baseline_service = BaselineService(db)
        self.scorer = AnomalyScorer()

    def analyze_chain(
        self, chain_id_str: str, user_id: Optional[UUID] = None, persist: bool = True
    ) -> BehavioralAnalysisResult:
        """
        Performs full behavioral analysis on an attack chain and optionally persists it.
        """
        logger.info(f"Starting behavioral analysis for chain {chain_id_str}")
        
        # Fetch chain and alerts
        chain = self.db.query(AttackChainDB).filter(AttackChainDB.chain_id == chain_id_str).first()
        if not chain:
            raise ValueError(f"Attack chain {chain_id_str} not found")
            
        # In a real impl, we'd fetch actual alerts. The chain has enough summary info for now.
        alerts = [] 
        
        # 1. Extract Features
        features = self.extractor.extract_features(chain, alerts)
        
        # 2. Get Baseline Context
        context = self.baseline_service.get_baseline_context(user_id, features)
        
        # 3. Score Dimensions
        dimensions: Dict[str, DimensionSignal] = {
            "identity": self.scorer.score_identity(features, context),
            "device": self.scorer.score_device(features, context),
            "network": self.scorer.score_network(features, context),
            "target": self.scorer.score_target(features, context),
            "behavior": self.scorer.score_behavior(features, context),
            "time": self.scorer.score_time(features, context),
            "history": self.scorer.score_history(features, context),
            "relationship": self.scorer.score_relationship(features, context),
        }
        
        # 4. Calculate Final Score
        total_score, level, top_signals, reason = self.scorer.calculate_total_anomaly(dimensions)
        
        result = BehavioralAnalysisResult(
            chain_id=chain_id_str,
            anomaly_score=round(total_score, 2),
            anomaly_level=level,
            signals=top_signals,
            dimension_breakdown=dimensions,
            why_prioritized=reason,
            source_ip=features.get("source_ip"),
            entity_context=context
        )

        # 5. Persist to DB if requested
        if persist:
            existing = self.db.query(BehavioralAnalysisDB).filter(
                BehavioralAnalysisDB.attack_chain_id == chain.id
            ).first()
            signals_json = json.dumps(top_signals)
            dim_json = json.dumps({k: v.model_dump() for k, v in dimensions.items()})
            int_score = int(round(total_score))

            if existing:
                existing.anomaly_score = int_score
                existing.anomaly_level = level
                existing.signals = signals_json
                existing.dimension_breakdown = dim_json
                existing.why_prioritized = reason
            else:
                record = BehavioralAnalysisDB(
                    attack_chain_id=chain.id,
                    anomaly_score=int_score,
                    anomaly_level=level,
                    signals=signals_json,
                    dimension_breakdown=dim_json,
                    why_prioritized=reason,
                )
                self.db.add(record)

            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to persist behavioral analysis for chain {chain_id_str}: {e}")
        
        logger.info(f"Completed behavioral analysis for {chain_id_str}: Score {result.anomaly_score} ({level})")
        return result

    def analyze_all_chains(
        self, user_id: Optional[UUID] = None, persist: bool = True
    ) -> List[BehavioralAnalysisResult]:
        """
        Analyzes all attack chains (optionally filtered by user_id) and persists the behavioral analysis records.
        """
        query = self.db.query(AttackChainDB)
        if user_id is not None:
            query = query.filter(AttackChainDB.user_id == user_id)
        chains = query.all()

        results = []
        for c in chains:
            try:
                res = self.analyze_chain(c.chain_id, user_id=c.user_id, persist=persist)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed to analyze chain {c.chain_id}: {e}")
        return results
