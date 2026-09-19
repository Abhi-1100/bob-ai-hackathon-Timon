"""
Production-Ready Alert Correlation Engine.

Deterministic, rule-based engine that converts raw alerts into grouped Attack Chains
based on source-IP affinity, time proximity, destination overlap, and attack progression.

This module does NOT use LLMs, LangGraph, or any AI. Correlation is fully deterministic.
"""

import logging
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from database.models import Alert as AlertDB, AttackChainDB, AttackChainEventDB
from repositories.attack_chain_repository import AttackChainRepository
from schemas.attack_chain import AttackChain, AttackChainAlert, CorrelationResult

logger = logging.getLogger("alert_correlation")

# Default correlation parameters
DEFAULT_TIME_WINDOW_MINUTES: int = 30

# Attack progression stages – earlier stages have lower indices.
# Used to sort events into a logical kill-chain order within a chain.
ATTACK_STAGE_ORDER: Dict[str, int] = {
    "Reconnaissance": 0,
    "PortScan": 1,
    "Enumeration": 2,
    "BruteForce": 3,
    "CredentialDumping": 4,
    "CredentialAccess": 5,
    "UnauthorizedAccess": 6,
    "PrivilegeEscalation": 7,
    "LateralMovement": 8,
    "C2Beacon": 9,
    "CommandExecution": 10,
    "RemoteCodeExecution": 11,
    "Malware": 12,
    "MalwareDownload": 13,
    "DataExfiltration": 14,
    "DDoS": 15,
    "DoS": 16,
    "Phishing": 17,
    "SQLInjection": 18,
}

# Severity weight for ordering within chains (higher = more severe)
SEVERITY_WEIGHT: Dict[str, int] = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}


class CorrelationError(Exception):
    """Raised when the correlation engine encounters a fatal issue."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AlertCorrelationEngine:
    """
    Rule-based correlation engine that groups raw alerts into attack chains.

    Pipeline:
        1. Fetch alerts from DB (sorted by timestamp).
        2. Group by source IP (hash-map O(n)).
        3. Apply time-window splitting within each IP group.
        4. Build AttackChain objects with event ordering.
        5. Optionally persist chains to the database.
    """

    def __init__(
        self,
        db: Session,
        time_window_minutes: int = DEFAULT_TIME_WINDOW_MINUTES,
    ):
        self.db = db
        self.time_window = timedelta(minutes=time_window_minutes)
        self.chain_repo = AttackChainRepository(db)

    def _next_chain_id(self, user_id: Optional[UUID]) -> str:
        """Allocate the next tenant-local human-readable chain id."""
        query = self.db.query(AttackChainDB)
        if user_id:
            query = query.filter(AttackChainDB.user_id == user_id)
        ids = [c.chain_id for c in query.all()]
        numbers = [int(value[2:]) for value in ids if value.startswith("AC") and value[2:].isdigit()]
        return f"AC{(max(numbers, default=0) + 1):03d}"

    def add_alert(self, alert: AlertDB, user_id: Optional[UUID] = None) -> AttackChainDB:
        """Incrementally attach one alert to an open chain.

        The bounds check is timestamp-based, so late-arriving events are placed
        correctly as long as they belong within the existing 30-minute window.
        """
        owner_id = user_id or alert.user_id
        query = self.db.query(AttackChainDB).filter(
            AttackChainDB.source_ip == alert.src_ip,
            AttackChainDB.status == "open",
        )
        if owner_id:
            query = query.filter(AttackChainDB.user_id == owner_id)
        chain = query.order_by(AttackChainDB.last_seen.desc()).first()

        if chain and chain.first_seen and chain.last_seen:
            outside_after = alert.timestamp > chain.last_seen + self.time_window
            outside_before = alert.timestamp < chain.first_seen - self.time_window
            if outside_after or outside_before:
                chain.status = "closed"
                self.db.flush()
                chain = None

        if chain is None:
            chain = AttackChainDB(
                id=uuid4(), user_id=owner_id, chain_id=self._next_chain_id(owner_id),
                source_ip=alert.src_ip, destination_ips=alert.dst_ip, events=alert.event,
                alert_count=0, start_time=alert.timestamp, end_time=alert.timestamp,
                status="open", first_seen=alert.timestamp, last_seen=alert.timestamp,
                event_counts=json.dumps({}),
            )
            self.db.add(chain)
            self.db.flush()

        linked = self.db.query(AttackChainEventDB).filter(
            AttackChainEventDB.chain_id == chain.id,
            AttackChainEventDB.alert_id == alert.id,
        ).first()
        if not linked:
            self.db.add(AttackChainEventDB(chain_id=chain.id, alert_id=alert.id))
            chain.alert_count = (chain.alert_count or 0) + 1

        linked_alerts = [link.alert for link in chain.chain_events if link.alert is not None]
        linked_alerts.append(alert)
        unique_alerts = {str(item.id): item for item in linked_alerts}.values()
        ordered = sorted(unique_alerts, key=lambda item: (item.timestamp, str(item.id)))
        counts: dict[str, int] = {}
        for item in ordered:
            counts[item.event] = counts.get(item.event, 0) + 1
        events = sorted(counts, key=lambda item: ATTACK_STAGE_ORDER.get(item, 999))
        chain.first_seen = min(item.timestamp for item in ordered)
        chain.last_seen = max(item.timestamp for item in ordered)
        chain.start_time = chain.first_seen
        chain.end_time = chain.last_seen
        chain.destination_ips = ",".join(sorted({item.dst_ip for item in ordered}))
        chain.events = ",".join(events)
        chain.event_counts = json.dumps(counts, sort_keys=True)
        self.db.commit()
        self.db.refresh(chain)
        return chain

    # ------------------------------------------------------------------
    # Step 1 – Fetch alerts
    # ------------------------------------------------------------------
    def _fetch_alerts(self, user_id: Optional[UUID] = None) -> List[AlertDB]:
        """Fetch alerts from the database ordered by timestamp, optionally scoped to a user."""
        query = self.db.query(AlertDB)
        if user_id:
            query = query.filter(AlertDB.user_id == user_id)
        alerts = query.order_by(AlertDB.timestamp.asc()).all()
        logger.info(f"Fetched {len(alerts)} alerts from database (user_id={user_id})")
        return alerts

    # ------------------------------------------------------------------
    # Step 2 – Group by source IP (O(n) hash-map)
    # ------------------------------------------------------------------
    @staticmethod
    def _group_by_source_ip(alerts: List[AlertDB]) -> Dict[str, List[AlertDB]]:
        """Group alerts into buckets keyed by source IP. O(n) via defaultdict."""
        groups: Dict[str, List[AlertDB]] = defaultdict(list)
        for alert in alerts:
            groups[alert.src_ip].append(alert)
        logger.debug(f"Grouped alerts into {len(groups)} source-IP buckets")
        return groups

    # ------------------------------------------------------------------
    # Step 3 – Split groups by time window
    # ------------------------------------------------------------------
    def _split_by_time_window(
        self, alerts: List[AlertDB]
    ) -> List[List[AlertDB]]:
        """
        Split a chronologically-sorted list of alerts into sub-chains
        whenever the gap between consecutive alerts exceeds the time window.
        """
        if not alerts:
            return []

        chains: List[List[AlertDB]] = []
        current_chain: List[AlertDB] = [alerts[0]]

        for prev, curr in zip(alerts, alerts[1:]):
            gap = curr.timestamp - prev.timestamp
            if gap <= self.time_window:
                current_chain.append(curr)
            else:
                chains.append(current_chain)
                current_chain = [curr]

        chains.append(current_chain)  # flush last chain
        return chains

    # ------------------------------------------------------------------
    # Step 4 – Build AttackChain schema objects
    # ------------------------------------------------------------------
    @staticmethod
    def _build_chain(
        chain_id: str,
        source_ip: str,
        alerts: List[AlertDB],
    ) -> AttackChain:
        """Convert a cluster of related AlertDB rows into an AttackChain Pydantic object."""

        # Collect unique destination IPs
        dst_ips = list({a.dst_ip for a in alerts})

        # Determine event progression order
        unique_events = list(dict.fromkeys(a.event for a in alerts))  # insertion-order unique
        unique_events.sort(key=lambda e: ATTACK_STAGE_ORDER.get(e, 999))

        # Severity summary
        severity_summary: Dict[str, int] = defaultdict(int)
        for a in alerts:
            severity_summary[a.severity] += 1

        # Timestamps
        start_time = min(a.timestamp for a in alerts)
        end_time = max(a.timestamp for a in alerts)

        # Alert detail list
        alert_details = [
            AttackChainAlert(
                alert_id=str(a.id),
                timestamp=a.timestamp,
                event=a.event,
                severity=a.severity,
                dst_ip=a.dst_ip,
            )
            for a in alerts
        ]

        return AttackChain(
            chain_id=chain_id,
            source_ip=source_ip,
            destination_ips=dst_ips,
            start_time=start_time,
            end_time=end_time,
            events=unique_events,
            severity_summary=dict(severity_summary),
            alert_count=len(alerts),
            alerts=alert_details,
        )

    # ------------------------------------------------------------------
    # Step 5 – Persist chains to DB
    # ------------------------------------------------------------------
    def _persist_chain(
        self,
        chain: AttackChain,
        alert_db_ids: List[UUID],
    ) -> AttackChainDB:
        """Store an AttackChain and its alert links in the database."""
        chain_record = self.chain_repo.create_chain(
            chain_id=chain.chain_id,
            source_ip=chain.source_ip,
            destination_ips=",".join(chain.destination_ips),
            events=",".join(chain.events),
            alert_count=chain.alert_count,
            start_time=chain.start_time,
            end_time=chain.end_time,
        )
        if alert_db_ids:
            self.chain_repo.bulk_add_alerts_to_chain(chain_record.id, alert_db_ids)
        return chain_record

    # ------------------------------------------------------------------
    # Public API – run full pipeline
    # ------------------------------------------------------------------
    def correlate(self, user_id: Optional[UUID] = None, persist: bool = True) -> CorrelationResult:
        """
        Execute the full correlation pipeline:
          1. Fetch alerts from DB (scoped to user_id if provided).
          2. Group by source IP.
          3. Split by time window.
          4. Build AttackChain objects.
          5. Optionally persist to DB with user_id attached.
          6. Return CorrelationResult.

        Raises:
            CorrelationError: If no alerts exist or a critical failure occurs.
        """
        start_ts = time.perf_counter()
        logger.info(f"Correlation started (user_id={user_id})")

        # 1. Fetch
        alerts = self._fetch_alerts(user_id=user_id)
        if not alerts:
            raise CorrelationError("No alerts found in the database to correlate")

        total_alerts = len(alerts)

        # 2. Group by source IP
        ip_groups = self._group_by_source_ip(alerts)

        # 3 + 4 – Split and build chains
        all_chains: List[AttackChain] = []
        all_alert_groups: List[List[AlertDB]] = []  # parallel list for persistence
        chain_counter = 0

        for src_ip, group_alerts in ip_groups.items():
            # Alerts within each IP group are already sorted by timestamp (from step 1)
            sub_chains = self._split_by_time_window(group_alerts)
            for sub_alerts in sub_chains:
                if not sub_alerts:
                    continue
                chain_counter += 1
                chain_id = f"AC{chain_counter:03d}"
                chain = self._build_chain(chain_id, src_ip, sub_alerts)
                all_chains.append(chain)
                all_alert_groups.append(sub_alerts)

        logger.info(f"Chains generated: {len(all_chains)} from {total_alerts} alerts (user_id={user_id})")

        # 5. Persist
        if persist:
            # Clear previous chains for this user to avoid duplicates on re-run
            try:
                self.chain_repo.delete_all_chains(user_id=user_id)
            except Exception:
                pass  # first run – nothing to delete

            logger.info("Bulk insert of attack chains started")
            chain_records: List[AttackChainDB] = []
            all_event_links: List[AttackChainEventDB] = []
            for chain, alert_group in zip(all_chains, all_alert_groups):
                alert_ids = [a.id for a in alert_group]
                chain_uuid = uuid4()
                chain_records.append(
                    AttackChainDB(
                        id=chain_uuid,
                        user_id=user_id,
                        chain_id=chain.chain_id,
                        source_ip=chain.source_ip,
                        destination_ips=",".join(chain.destination_ips),
                        events=",".join(chain.events),
                        alert_count=chain.alert_count,
                        start_time=chain.start_time,
                        end_time=chain.end_time,
                        status="open",
                        first_seen=chain.start_time,
                        last_seen=chain.end_time,
                        event_counts=json.dumps({event: sum(1 for item in alert_group if item.event == event) for event in chain.events}, sort_keys=True),
                    )
                )
                for aid in alert_ids:
                    all_event_links.append(AttackChainEventDB(chain_id=chain_uuid, alert_id=aid))

            if chain_records:
                self.db.bulk_save_objects(chain_records)
            if all_event_links:
                self.db.bulk_save_objects(all_event_links)
            try:
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                logger.error(f"Failed to commit bulk attack chains: {exc}")
            logger.info("Bulk insert of attack chains completed")

        elapsed_ms = (time.perf_counter() - start_ts) * 1000

        result = CorrelationResult(
            chains_created=len(all_chains),
            alerts_processed=total_alerts,
            execution_time_ms=round(elapsed_ms, 2),
            chains=all_chains,
        )

        logger.info(
            f"Correlation completed: chains={result.chains_created}, "
            f"alerts={result.alerts_processed}, time={result.execution_time_ms}ms"
        )
        return result
