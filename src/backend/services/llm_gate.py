"""Cooldown-aware, bounded LLM job queue for completed deterministic chains."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

from database.session import SessionLocal
from database.models import AttackChainDB

logger = logging.getLogger("llm_gate")


@dataclass(frozen=True)
class LLMJob:
    user_id: Any
    chain_id: str
    reason: str


class LLMJobQueue:
    """Runs at most one report workflow at a time and enforces a 2-minute cooldown."""

    def __init__(self, publisher: Callable[[Any, dict], Awaitable[None]]) -> None:
        self.queue: asyncio.Queue[LLMJob] = asyncio.Queue(maxsize=100)
        self.publisher = publisher
        self.task: asyncio.Task | None = None
        self.last_queued: dict[tuple[str, str], datetime] = {}

    async def start(self) -> None:
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._worker(), name="timontrack-llm-worker")

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def enqueue(self, user_id: Any, chain_id: str, reason: str) -> bool:
        key = (str(user_id), chain_id)
        now = datetime.now(timezone.utc)
        previous = self.last_queued.get(key)
        if previous and now - previous < timedelta(minutes=2):
            return False
        self.last_queued[key] = now
        try:
            self.queue.put_nowait(LLMJob(user_id=user_id, chain_id=chain_id, reason=reason))
            return True
        except asyncio.QueueFull:
            logger.warning("LLM queue full; dropping job chain_id=%s", chain_id)
            return False

    async def _worker(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                await asyncio.to_thread(self._run_job, job)
                await self.publisher(job.user_id, {"type": "llm_report_ready", "chain_id": job.chain_id, "reason": job.reason})
            except Exception:
                logger.exception("LLM report job failed for chain_id=%s", job.chain_id)
            finally:
                self.queue.task_done()

    @staticmethod
    def _run_job(job: LLMJob) -> None:
        """Invoke the existing workflow only after deterministic gating."""
        with SessionLocal() as db:
            chain = db.query(AttackChainDB).filter(
                AttackChainDB.chain_id == job.chain_id,
                AttackChainDB.user_id == job.user_id,
            ).first()
            if not chain:
                return
            last_run = chain.last_llm_run
            if last_run and datetime.now(timezone.utc) - last_run < timedelta(minutes=2):
                logger.info("Skipping LLM job inside cooldown chain_id=%s", job.chain_id)
                return
            from graph.threat_workflow import ThreatWorkflowRunner
            ThreatWorkflowRunner(db=db, user_id=job.user_id).run(job.chain_id)
            chain.last_llm_run = datetime.now(timezone.utc)
            db.commit()
