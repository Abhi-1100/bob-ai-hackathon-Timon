"""In-process queue, deterministic pipeline worker, and tenant event broker."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from database.models import Alert as AlertDB, AttackChainDB, ConnectorDB
from database.session import SessionLocal
from repositories.risk_repository import RiskRepository
from services.alert_correlation import AlertCorrelationEngine
from services.mitre_mapping import MitreMappingService
from services.risk_scoring import RiskScoringEngine
from services.llm_gate import LLMJobQueue
from services.metrics import metrics
from services.connectors import FileTailerConnector
from services.ingestion import ingest_raw_events

logger = logging.getLogger("live_runtime")


@dataclass(frozen=True)
class AlertJob:
    user_id: Any
    alert_id: Any


class LiveRuntime:
    """Coordinates ingestion jobs and tenant-scoped SSE subscribers."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[AlertJob] = asyncio.Queue()
        self.subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self.worker_task: asyncio.Task | None = None
        self.stop_event = asyncio.Event()
        self.sweeper_task: asyncio.Task | None = None
        self.llm_queue = LLMJobQueue(self.publish)
        self.connector_tasks: dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        if self.worker_task is None or self.worker_task.done():
            self.stop_event.clear()
            self.worker_task = asyncio.create_task(self._worker(), name="timontrack-pipeline-worker")
            self.sweeper_task = asyncio.create_task(self._sweeper(), name="timontrack-chain-sweeper")
            await self.llm_queue.start()
            await self._start_enabled_connectors()

    async def stop(self) -> None:
        self.stop_event.set()
        for task in list(self.connector_tasks.values()):
            task.cancel()
        if self.connector_tasks:
            await asyncio.gather(*self.connector_tasks.values(), return_exceptions=True)
            self.connector_tasks.clear()
        if self.worker_task:
            await self.worker_task
            self.worker_task = None
        if self.sweeper_task:
            self.sweeper_task.cancel()
            try:
                await self.sweeper_task
            except asyncio.CancelledError:
                pass
            self.sweeper_task = None
        await self.llm_queue.stop()

    async def enqueue(self, user_id: Any, alert_id: Any) -> None:
        await self.queue.put(AlertJob(user_id=user_id, alert_id=alert_id))

    async def _start_enabled_connectors(self) -> None:
        try:
            records = await asyncio.to_thread(self._enabled_connector_configs)
            for connector_id, user_id, config, connector_type, cursor in records:
                await self.start_connector(connector_id, user_id, config, connector_type, cursor)
        except Exception:
            logger.exception("Unable to start enabled connectors")

    @staticmethod
    def _enabled_connector_configs():
        with SessionLocal() as db:
            rows = db.query(ConnectorDB).filter_by(status="enabled").all()
            return [(str(row.id), row.user_id, json.loads(row.config or "{}"), row.type, row.cursor) for row in rows]

    async def start_connector(self, connector_id: str, user_id: Any, config: dict[str, Any], connector_type: str, cursor: str | None = None) -> None:
        """Start one persisted connector; only file tailing is enabled in this phase."""
        if connector_id in self.connector_tasks:
            return
        if connector_type not in {"file_tail", "file_tailer"}:
            raise ValueError(f"Unsupported connector type '{connector_type}'")
        task = asyncio.create_task(self._connector_loop(connector_id, user_id, config, cursor), name=f"connector-{connector_id}")
        self.connector_tasks[connector_id] = task

    async def stop_connector(self, connector_id: str) -> None:
        task = self.connector_tasks.pop(connector_id, None)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def _connector_loop(self, connector_id: str, user_id: Any, config: dict[str, Any], cursor: str | None = None) -> None:
        connector = FileTailerConnector(config["path"])
        interval = max(1.0, float(config.get("interval", 10)))
        while not self.stop_event.is_set():
            events = await connector.fetch(cursor)
            next_cursor = getattr(connector, "cursor", cursor)
            if events:
                alert_ids = await asyncio.to_thread(self._persist_connector_batch, connector_id, user_id, config.get("source", "generic"), events, next_cursor)
                for alert_id in alert_ids:
                    await self.enqueue(user_id, alert_id)
            else:
                await asyncio.to_thread(self._save_connector_cursor, connector_id, user_id, next_cursor, 0)
            cursor = next_cursor
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    @staticmethod
    def _persist_connector_batch(connector_id, user_id, source, events, cursor):
        with SessionLocal() as db:
            alert_ids = []
            result = ingest_raw_events(db, user_id, source, events, queue=lambda _uid, alert_id: alert_ids.append(alert_id))
            LiveRuntime._save_connector_cursor(connector_id, user_id, cursor, result["accepted"], db=db)
            return alert_ids

    @staticmethod
    def _save_connector_cursor(connector_id, user_id, cursor, accepted, db=None):
        owns_db = db is None
        if owns_db:
            db = SessionLocal()
        try:
            record = db.query(ConnectorDB).filter(ConnectorDB.id == connector_id, ConnectorDB.user_id == user_id).first()
            if record:
                record.cursor = cursor
                record.last_sync = datetime.now(timezone.utc)
                record.events_ingested = (record.events_ingested or 0) + accepted
            db.commit()
        finally:
            if owns_db:
                db.close()

    def subscribe(self, user_id: Any) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self.subscribers[str(user_id)].add(queue)
        return queue

    def unsubscribe(self, user_id: Any, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.subscribers[str(user_id)].discard(queue)

    async def publish(self, user_id: Any, event: dict[str, Any]) -> None:
        for queue in list(self.subscribers.get(str(user_id), ())):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Dropping live event for slow tenant subscriber user_id=%s", user_id)

    async def _worker(self) -> None:
        while not self.stop_event.is_set():
            try:
                job = await asyncio.wait_for(self.queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            try:
                event = await asyncio.to_thread(self._process, job)
                await self.publish(job.user_id, event)
                if event.get("llm_reason"):
                    await self.llm_queue.enqueue(job.user_id, event["chain_id"], event["llm_reason"])
            except Exception:
                logger.exception("Streaming pipeline job failed for user_id=%s alert_id=%s", job.user_id, job.alert_id)
            finally:
                self.queue.task_done()

    async def _sweeper(self) -> None:
        while not self.stop_event.is_set():
            try:
                closed = await asyncio.to_thread(self._close_stale_chains)
                for user_id, chain_id in closed:
                    await self.llm_queue.enqueue(user_id, chain_id, "close")
                    await self.publish(user_id, {"type": "chain_closed", "chain_id": chain_id, "user_id": str(user_id)})
            except Exception:
                logger.exception("Chain sweeper failed")
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                pass

    @staticmethod
    def _close_stale_chains() -> list[tuple[Any, str]]:
        from datetime import datetime, timedelta, timezone
        with SessionLocal() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
            chains = db.query(AttackChainDB).filter(AttackChainDB.status == "open").all()
            closed = []
            for chain in chains:
                last_seen = chain.last_seen or chain.end_time
                if last_seen and last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                if last_seen and last_seen < cutoff:
                    chain.status = "closed"
                    closed.append((chain.user_id, chain.chain_id))
            db.commit()
            return closed

    @staticmethod
    def _process(job: AlertJob) -> dict[str, Any]:
        with SessionLocal() as db:
            alert = db.query(AlertDB).filter(AlertDB.id == job.alert_id, AlertDB.user_id == job.user_id).first()
            if not alert:
                raise ValueError("queued alert no longer exists in tenant scope")
            engine = AlertCorrelationEngine(db)
            previous_tier = None
            chain = engine.add_alert(alert, job.user_id)
            previous_tier = chain.tier
            mapper = MitreMappingService(db)
            mapping = mapper.map_attack_chain(chain)
            mapper.store_mappings(chain, mapping)
            scorer = RiskScoringEngine(db)
            score = scorer.score_chain_data(chain.chain_id, [e for e in (chain.events or "").split(",") if e], chain.mitre_mappings)
            RiskRepository(db).save_risk_score(chain.id, score.score, score.level, score.reasoning, score.event_score, score.mitre_score, score.chain_bonus)
            chain.risk_score_value = score.score
            chain.tier = score.level
            db.commit()
            tier_rank = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
            llm_reason = (
                "tier_escalation"
                if previous_tier is not None and tier_rank.get(score.level, 0) > tier_rank.get(previous_tier, -1)
                else None
            )
            metrics.mark_processed(str(job.alert_id))
            metrics.chains = max(metrics.chains, db.query(AttackChainDB).filter(AttackChainDB.user_id == job.user_id).count())
            return {
                "type": "chain_updated",
                "chain_id": chain.chain_id,
                "user_id": str(job.user_id),
                "status": chain.status,
                "risk_score": score.score,
                "tier": score.level,
                "event_counts": json.loads(chain.event_counts or "{}"),
                "llm_reason": llm_reason,
            }


runtime = LiveRuntime()
