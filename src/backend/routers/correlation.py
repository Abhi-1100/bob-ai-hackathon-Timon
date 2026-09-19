"""
Correlation router – exposes the alert correlation engine and attack chain queries via FastAPI.
"""

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.session import get_db
from database.models import (
    AttackChainDB, Alert as AlertDB, MitreMappingDB, RiskScoreDB,
    ReportDB, RecommendationDB, UserDB
)
from routers.auth import get_current_user_obj
from schemas.attack_chain import CorrelationResult
from schemas.upload import ErrorResponse
from services.alert_correlation import AlertCorrelationEngine, CorrelationError

logger = logging.getLogger("correlation_router")

router = APIRouter(
    prefix="/api/v1/chains",
    tags=["Alert Correlation"],
)


from services.cache_service import cache
from sqlalchemy.orm import joinedload, selectinload

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get All Correlated Attack Chains",
    description="Returns all persisted attack chains from the database, or empty list if no alerts have been ingested."
)
def get_attack_chains(
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Fetch all attack chains from the database without re-running correlation."""
    cache_key = f"all_attack_chains_{current_user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    chains = (
        db.query(AttackChainDB)
        .filter(AttackChainDB.user_id == current_user.id)
        .options(
            joinedload(AttackChainDB.risk_score),
            selectinload(AttackChainDB.mitre_mappings),
        )
        .order_by(AttackChainDB.start_time.desc())
        .all()
    )
    results = []

    for c in chains:
        dest_ips = [ip.strip() for ip in (c.destination_ips or "").split(",") if ip.strip()]
        events_list = [e.strip() for e in (c.events or "").split(",") if e.strip()]

        # Map mitre techniques
        mitre_list = [
            {
                "technique_id": m.technique_id,
                "name": m.technique_name,
                "tactic": m.tactic,
                "event": m.event,
            }
            for m in (c.mitre_mappings or [])
        ]

        # Extract risk score
        risk_score = c.risk_score.score if c.risk_score else 0
        severity = c.risk_score.level if c.risk_score else "Medium"

        results.append({
            "chain_id": c.chain_id,
            "source_ip": c.source_ip,
            "dest_ips": dest_ips,
            "events": events_list,
            "alert_count": c.alert_count,
            "start_time": c.start_time.isoformat() if c.start_time else None,
            "end_time": c.end_time.isoformat() if c.end_time else None,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if c.created_at else None,
            "risk_score": risk_score,
            "final_score": risk_score,
            "severity": severity,
            "risk_level": severity,
            "behavioral_score": c.risk_score.behavioral_score if c.risk_score else None,
            "behavioral_level": c.risk_score.behavioral_level if c.risk_score else None,
            "status": "Active",
            "mitre_techniques": mitre_list,
        })

    payload = {
        "chains": results,
        "count": len(results),
    }
    cache.set(cache_key, payload, ttl=300.0)
    return payload


@router.get(
    "/generate",
    status_code=status.HTTP_200_OK,
    summary="Generate Attack Chains",
    description="Runs rule-based correlation on all stored alerts and persists new attack chains."
)
def generate_attack_chains(
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Run correlation pipeline and return chains."""
    try:
        engine = AlertCorrelationEngine(db=db)
        result = engine.correlate(user_id=current_user.id, persist=True)
        cache.delete(f"all_attack_chains_{current_user.id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(mode="json"),
        )
    except CorrelationError as ce:
        logger.info(f"Correlation check: {ce.message}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"chains": [], "total_chains": 0, "execution_time_ms": 0.0, "message": ce.message},
        )
    except Exception as exc:
        logger.error(f"Unexpected error during correlation: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="An unexpected error occurred during correlation",
            ).model_dump(),
        )


@router.get(
    "/{chain_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Attack Chain by ID",
    description="Returns detailed attack chain records with full event progression and telemetry."
)
def get_attack_chain_by_id(
    chain_id: str,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Retrieve full details of an attack chain."""
    chain = (
        db.query(AttackChainDB)
        .filter(
            AttackChainDB.chain_id == chain_id,
            (AttackChainDB.user_id == current_user.id) | (AttackChainDB.user_id.is_(None))
        )
        .first()
    )
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attack chain '{chain_id}' not found")

    # On-demand behavioral context analysis if not yet generated
    if not chain.behavioral_analysis:
        try:
            from services.behavioral_analysis import BehavioralAnalysisEngine
            ba_engine = BehavioralAnalysisEngine(db=db)
            ba_engine.analyze_chain(chain.chain_id, user_id=chain.user_id, persist=True)
            db.refresh(chain)
        except Exception as exc:
            logger.warning(f"On-demand behavioral analysis generation failed for {chain_id}: {exc}")

    dest_ips = [ip.strip() for ip in (chain.destination_ips or "").split(",") if ip.strip()]

    # Extract linked events from junction table
    linked_alerts = []
    for junction in chain.chain_events:
        alert = junction.alert
        if alert:
            linked_alerts.append({
                "timestamp": alert.timestamp.isoformat() if alert.timestamp else "",
                "event": alert.event,
                "severity": alert.severity,
                "src_ip": alert.src_ip,
                "dst_ip": alert.dst_ip,
                "source_type": alert.source_type,
                "protocol": "TCP",
            })

    # If junction events empty, parse from comma separated events
    if not linked_alerts and chain.events:
        for ev in chain.events.split(","):
            if ev.strip():
                linked_alerts.append({
                    "timestamp": chain.start_time.isoformat() if chain.start_time else "",
                    "event": ev.strip(),
                    "severity": chain.risk_score.level if chain.risk_score else "Medium",
                    "src_ip": chain.source_ip,
                    "dst_ip": dest_ips[0] if dest_ips else "10.0.0.1",
                    "protocol": "TCP",
                })

    # Mitre mappings
    mitre_techniques = [
        {
            "technique_id": m.technique_id,
            "name": m.technique_name,
            "tactic": m.tactic,
            "count": 1,
        }
        for m in (chain.mitre_mappings or [])
    ]

    # Risk score breakdown
    score = chain.risk_score.score if chain.risk_score else 50
    sev = chain.risk_score.level if chain.risk_score else "Medium"
    behavioral_score_val = (
        chain.risk_score.behavioral_score 
        if (chain.risk_score and chain.risk_score.behavioral_score is not None) 
        else (chain.behavioral_analysis.anomaly_score if chain.behavioral_analysis else None)
    )
    breakdown = {
        "base_event_score": chain.risk_score.event_score if chain.risk_score else 25,
        "mitre_score": chain.risk_score.mitre_score if chain.risk_score else 15,
        "kill_chain_bonus": chain.risk_score.chain_bonus if chain.risk_score else 10,
        "behavioral_score": behavioral_score_val,
        "final_score": score,
    }

    # Contextual Behavioral Analysis
    behavioral_context = None
    if chain.behavioral_analysis:
        ba = chain.behavioral_analysis
        signals_list = []
        if ba.signals:
            try:
                signals_list = json.loads(ba.signals) if isinstance(ba.signals, str) else ba.signals
            except Exception:
                pass
        dim_breakdown = {}
        if ba.dimension_breakdown:
            try:
                dim_breakdown = json.loads(ba.dimension_breakdown) if isinstance(ba.dimension_breakdown, str) else ba.dimension_breakdown
            except Exception:
                pass
        behavioral_context = {
            "anomaly_score": ba.anomaly_score,
            "anomaly_level": ba.anomaly_level,
            "signals": signals_list,
            "contributing_signals": signals_list,
            "dimension_breakdown": dim_breakdown,
            "why_prioritized": ba.why_prioritized,
        }

    # Recommendations
    recs_obj = None
    if chain.recommendation:
        try:
            recs_obj = {
                "immediate_actions": json.loads(chain.recommendation.immediate_actions) if isinstance(chain.recommendation.immediate_actions, str) else chain.recommendation.immediate_actions,
                "containment_actions": json.loads(chain.recommendation.containment_actions) if isinstance(chain.recommendation.containment_actions, str) else chain.recommendation.containment_actions,
                "investigation_actions": json.loads(chain.recommendation.investigation_actions) if isinstance(chain.recommendation.investigation_actions, str) else chain.recommendation.investigation_actions,
                "prevention_actions": json.loads(chain.recommendation.prevention_actions) if isinstance(chain.recommendation.prevention_actions, str) else chain.recommendation.prevention_actions,
            }
        except Exception:
            pass

    # Executive report
    report_obj = None
    if chain.report:
        report_obj = {
            "threat_level": chain.report.threat_level,
            "executive_summary": chain.report.executive_summary,
            "attack_overview": chain.report.attack_overview,
            "affected_assets": chain.report.affected_assets,
            "mitre_summary": chain.report.mitre_summary,
            "risk_assessment": chain.report.risk_assessment,
            "recommended_actions": chain.report.recommended_actions,
            "conclusion": chain.report.conclusion,
        }

    return {
        "chain_id": chain.chain_id,
        "source_ip": chain.source_ip,
        "dest_ips": dest_ips,
        "alert_count": chain.alert_count,
        "start_time": chain.start_time.isoformat() if chain.start_time else None,
        "end_time": chain.end_time.isoformat() if chain.end_time else None,
        "severity": sev,
        "risk_level": sev,
        "risk_score": score,
        "final_score": score,
        "behavioral_score": behavioral_score_val if behavioral_score_val is not None else (chain.behavioral_analysis.anomaly_score if chain.behavioral_analysis else None),
        "behavioral_level": (chain.risk_score.behavioral_level if chain.risk_score and chain.risk_score.behavioral_level else (chain.behavioral_analysis.anomaly_level if chain.behavioral_analysis else None)),
        "behavioral_context": behavioral_context,
        "score_breakdown": breakdown,
        "events": linked_alerts,
        "mitre_techniques": mitre_techniques,
        "recommendations": recs_obj,
        "report": report_obj,
        "status": "Active",
    }


@router.post(
    "/{chain_id}/behavioral",
    status_code=status.HTTP_200_OK,
    summary="Generate or Refresh Behavioral Analysis for Chain",
    description="Forces on-demand behavioral anomaly calculation for the specified attack chain."
)
def generate_behavioral_analysis(
    chain_id: str,
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """Run on-demand behavioral analysis for a specific chain."""
    chain = (
        db.query(AttackChainDB)
        .filter(
            AttackChainDB.chain_id == chain_id,
            (AttackChainDB.user_id == current_user.id) | (AttackChainDB.user_id.is_(None))
        )
        .first()
    )
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attack chain '{chain_id}' not found")

    from services.behavioral_analysis import BehavioralAnalysisEngine
    ba_engine = BehavioralAnalysisEngine(db=db)
    result = ba_engine.analyze_chain(chain.chain_id, user_id=chain.user_id, persist=True)
    cache.delete(f"all_attack_chains_{current_user.id}")
    return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump(mode="json"))

