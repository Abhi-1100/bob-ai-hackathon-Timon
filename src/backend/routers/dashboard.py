"""
Dashboard & Analytics router.
Provides dynamic real-time telemetry, KPI summaries, risk distribution,
MITRE frequency, timeline series, and database reset endpoint.
All data is 100% computed from the database (0 static mock data).
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc

from database.session import get_db
from database.models import (
    Alert as AlertDB,
    AttackChainDB,
    AttackChainEventDB,
    MitreMappingDB,
    RiskScoreDB,
    RecommendationDB,
    ReportDB,
    Upload as UploadDB,
)

logger = logging.getLogger("dashboard_router")

router = APIRouter(
    prefix="/api/v1",
    tags=["Dashboard & Analytics"],
)


@router.get(
    "/dashboard/stats",
    status_code=status.HTTP_200_OK,
    summary="Get Dynamic Dashboard Statistics & KPIs",
    description="Returns dynamic SOC dashboard statistics aggregated from database alerts and attack chains.",
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Fetch 100% dynamic dashboard KPIs and telemetry charts."""
    try:
        total_alerts = db.query(func.count(AlertDB.id)).scalar() or 0
        total_chains = db.query(func.count(AttackChainDB.id)).scalar() or 0

        # Risk severity breakdown from RiskScoreDB
        crit_count = (
            db.query(func.count(RiskScoreDB.id))
            .filter(RiskScoreDB.level == "Critical")
            .scalar()
            or 0
        )
        high_count = (
            db.query(func.count(RiskScoreDB.id))
            .filter(RiskScoreDB.level == "High")
            .scalar()
            or 0
        )
        med_count = (
            db.query(func.count(RiskScoreDB.id))
            .filter(RiskScoreDB.level == "Medium")
            .scalar()
            or 0
        )
        low_count = (
            db.query(func.count(RiskScoreDB.id))
            .filter(RiskScoreDB.level == "Low")
            .scalar()
            or 0
        )

        avg_score_raw = db.query(func.avg(RiskScoreDB.score)).scalar()
        avg_risk_score = round(float(avg_score_raw), 1) if avg_score_raw else 0.0

        # Unique MITRE techniques detected
        mitre_techniques_count = (
            db.query(func.count(distinct(MitreMappingDB.technique_id))).scalar() or 0
        )

        # Risk distribution for donut / pie chart
        risk_distribution = [
            {"name": "Critical", "value": crit_count, "color": "#EF4444"},
            {"name": "High", "value": high_count, "color": "#F97316"},
            {"name": "Medium", "value": med_count, "color": "#FBBF24"},
            {"name": "Low", "value": low_count, "color": "#10B981"},
        ]

        # Top MITRE technique frequencies
        mitre_counts = (
            db.query(
                MitreMappingDB.technique_id,
                MitreMappingDB.technique_name,
                MitreMappingDB.tactic,
                func.count(MitreMappingDB.id).label("freq"),
            )
            .group_by(
                MitreMappingDB.technique_id,
                MitreMappingDB.technique_name,
                MitreMappingDB.tactic,
            )
            .order_by(desc("freq"))
            .limit(10)
            .all()
        )

        mitre_frequency = [
            {
                "technique_id": m.technique_id,
                "name": f"{m.technique_id} {m.technique_name}",
                "count": m.freq,
                "tactic": m.tactic or "Unknown",
            }
            for m in mitre_counts
        ]

        # Timeline generation from alert timestamps
        timeline_query = (
            db.query(
                AlertDB.timestamp,
                AlertDB.severity,
            )
            .order_by(AlertDB.timestamp.asc())
            .limit(2000)
            .all()
        )

        hourly_buckets = defaultdict(lambda: {"alerts": 0, "critical": 0, "high": 0})
        for al in timeline_query:
            if al.timestamp:
                bucket_key = al.timestamp.strftime("%m-%d %H:00")
                hourly_buckets[bucket_key]["alerts"] += 1
                if al.severity == "Critical":
                    hourly_buckets[bucket_key]["critical"] += 1
                elif al.severity == "High":
                    hourly_buckets[bucket_key]["high"] += 1

        timeline = [
            {
                "time": time_key,
                "alerts": data["alerts"],
                "critical": data["critical"],
                "high": data["high"],
            }
            for time_key, data in list(hourly_buckets.items())[-14:]  # Last 14 hours/intervals
        ]

        # Recent incidents (latest 10 chains)
        recent_chains_db = (
            db.query(AttackChainDB)
            .order_by(AttackChainDB.start_time.desc())
            .limit(10)
            .all()
        )

        recent_incidents = []
        for c in recent_chains_db:
            score = c.risk_score.score if c.risk_score else 0
            level = c.risk_score.level if c.risk_score else "Medium"
            mitre_list = [
                {
                    "technique_id": m.technique_id,
                    "name": m.technique_name,
                    "tactic": m.tactic,
                }
                for m in (c.mitre_mappings or [])
            ]
            dest_ips = [
                ip.strip() for ip in (c.destination_ips or "").split(",") if ip.strip()
            ]
            recent_incidents.append(
                {
                    "chain_id": c.chain_id,
                    "source_ip": c.source_ip,
                    "dest_ips": dest_ips,
                    "alert_count": c.alert_count,
                    "risk_score": score,
                    "severity": level,
                    "status": "Active",
                    "created_at": (
                        c.created_at.strftime("%Y-%m-%d %H:%M UTC")
                        if c.created_at
                        else None
                    ),
                    "mitre_techniques": mitre_list,
                }
            )

        # Noise reduction calculation
        noise_reduction = 0.0
        if total_alerts > 0 and total_chains > 0:
            noise_reduction = round((1 - (total_chains / total_alerts)) * 100, 1)

        return {
            "total_alerts": total_alerts,
            "total_chains": total_chains,
            "critical_incidents": crit_count,
            "high_risk_incidents": high_count,
            "medium_risk_incidents": med_count,
            "low_risk_incidents": low_count,
            "mitre_techniques_count": mitre_techniques_count,
            "avg_risk_score": avg_risk_score,
            "noise_reduction": max(0.0, noise_reduction),
            "risk_distribution": risk_distribution,
            "mitre_frequency": mitre_frequency,
            "timeline": timeline,
            "recent_incidents": recent_incidents,
        }

    except Exception as exc:
        logger.error(f"Error computing dashboard stats: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to compute dashboard stats: {str(exc)}"},
        )


@router.get(
    "/analytics/overview",
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Security Analytics & Telemetry",
    description="Aggregates attack stage events, severity levels, top attacker IPs, and target breakdown.",
)
def get_analytics_overview(db: Session = Depends(get_db)):
    """Fetch telemetry analytics aggregated strictly from stored alerts."""
    try:
        total_alerts = db.query(func.count(AlertDB.id)).scalar() or 0
        total_chains = db.query(func.count(AttackChainDB.id)).scalar() or 0
        unique_sources = (
            db.query(func.count(distinct(AlertDB.src_ip))).scalar() or 0
        )
        unique_destinations = (
            db.query(func.count(distinct(AlertDB.dst_ip))).scalar() or 0
        )

        # Attack progression / event type breakdown
        event_query = (
            db.query(AlertDB.event, AlertDB.severity, func.count(AlertDB.id).label("count"))
            .group_by(AlertDB.event, AlertDB.severity)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        attack_types = [
            {
                "name": eq.event,
                "count": eq.count,
                "level": eq.severity or "Medium",
            }
            for eq in event_query
        ]

        # Severity breakdown
        sev_query = (
            db.query(AlertDB.severity, func.count(AlertDB.id).label("count"))
            .group_by(AlertDB.severity)
            .order_by(desc("count"))
            .all()
        )
        severity_breakdown = [
            {"severity": sq.severity, "count": sq.count} for sq in sev_query
        ]

        # Top source attacker IPs
        src_query = (
            db.query(AlertDB.src_ip, func.count(AlertDB.id).label("count"))
            .group_by(AlertDB.src_ip)
            .order_by(desc("count"))
            .limit(8)
            .all()
        )
        top_sources = [{"ip": sq.src_ip, "count": sq.count} for sq in src_query]

        # Top target IPs
        dst_query = (
            db.query(AlertDB.dst_ip, func.count(AlertDB.id).label("count"))
            .group_by(AlertDB.dst_ip)
            .order_by(desc("count"))
            .limit(8)
            .all()
        )
        top_targets = [{"ip": dq.dst_ip, "count": dq.count} for dq in dst_query]

        # MITRE frequency
        mitre_counts = (
            db.query(
                MitreMappingDB.technique_id,
                MitreMappingDB.technique_name,
                MitreMappingDB.tactic,
                func.count(MitreMappingDB.id).label("freq"),
            )
            .group_by(
                MitreMappingDB.technique_id,
                MitreMappingDB.technique_name,
                MitreMappingDB.tactic,
            )
            .order_by(desc("freq"))
            .limit(8)
            .all()
        )
        mitre_frequency = [
            {
                "technique_id": m.technique_id,
                "name": f"{m.technique_id} {m.technique_name}",
                "count": m.freq,
                "tactic": m.tactic or "Unknown",
            }
            for m in mitre_counts
        ]

        # Hourly trend
        alerts_timeline = (
            db.query(AlertDB.timestamp, AlertDB.severity)
            .order_by(AlertDB.timestamp.asc())
            .limit(2000)
            .all()
        )
        buckets = defaultdict(lambda: {"alerts": 0, "critical": 0, "high": 0})
        for al in alerts_timeline:
            if al.timestamp:
                b_key = al.timestamp.strftime("%m-%d %H:00")
                buckets[b_key]["alerts"] += 1
                if al.severity == "Critical":
                    buckets[b_key]["critical"] += 1
                elif al.severity == "High":
                    buckets[b_key]["high"] += 1

        trend_data = [
            {
                "time": k,
                "alerts": v["alerts"],
                "critical": v["critical"],
                "high": v["high"],
            }
            for k, v in list(buckets.items())[-12:]
        ]

        return {
            "total_alerts": total_alerts,
            "total_chains": total_chains,
            "unique_sources": unique_sources,
            "unique_destinations": unique_destinations,
            "attack_types": attack_types,
            "severity_breakdown": severity_breakdown,
            "top_sources": top_sources,
            "top_targets": top_targets,
            "mitre_frequency": mitre_frequency,
            "trend_data": trend_data,
        }

    except Exception as exc:
        logger.error(f"Error computing analytics overview: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to compute analytics: {str(exc)}"},
        )


@router.post(
    "/dashboard/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset All Ingested Data and Correlated Incidents",
    description="Wipes all alerts, uploads, attack chains, MITRE mappings, risk scores, recommendations, and reports to return system to 0 state.",
)
def reset_system_data(db: Session = Depends(get_db)):
    """Wipe all user ingested data and correlation state for fresh CSV testing."""
    try:
        # Delete children tables first
        db.query(AttackChainEventDB).delete(synchronize_session=False)
        db.query(MitreMappingDB).delete(synchronize_session=False)
        db.query(RiskScoreDB).delete(synchronize_session=False)
        db.query(RecommendationDB).delete(synchronize_session=False)
        db.query(ReportDB).delete(synchronize_session=False)
        db.query(AttackChainDB).delete(synchronize_session=False)
        db.query(AlertDB).delete(synchronize_session=False)
        db.query(UploadDB).delete(synchronize_session=False)

        db.commit()
        logger.info("Successfully wiped all database tables to 0 records.")

        return {
            "success": True,
            "message": "All data cleared successfully. System is in 0-state ready for user CSV upload.",
            "total_alerts": 0,
            "total_chains": 0,
        }

    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to reset database: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"Reset failed: {str(exc)}"},
        )
