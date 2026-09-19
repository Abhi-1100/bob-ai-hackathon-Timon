"""Lightweight process metrics for the live demo and dashboard."""

from __future__ import annotations

import time
from collections import deque


class LiveMetrics:
    def __init__(self) -> None:
        self.ingested = 0
        self.processed = 0
        self.chains = 0
        self.latencies_ms: deque[float] = deque(maxlen=1000)
        self._ingest_times: dict[str, float] = {}

    def mark_ingested(self, alert_id: str) -> None:
        self.ingested += 1
        self._ingest_times[alert_id] = time.perf_counter()

    def mark_processed(self, alert_id: str) -> None:
        self.processed += 1
        started = self._ingest_times.pop(alert_id, None)
        if started is not None:
            self.latencies_ms.append((time.perf_counter() - started) * 1000)

    def snapshot(self) -> dict[str, float | int]:
        return {
            "alerts_ingested": self.ingested,
            "alerts_processed": self.processed,
            "chains_seen": self.chains,
            "noise_reduction_percent": round((1 - self.chains / self.ingested) * 100, 2) if self.ingested else 0.0,
            "ingest_to_dashboard_latency_ms": round(sum(self.latencies_ms) / len(self.latencies_ms), 2) if self.latencies_ms else 0.0,
        }


metrics = LiveMetrics()
