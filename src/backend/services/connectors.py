"""Async connector abstractions and a rotation-safe JSON-lines file tailer."""

from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Awaitable, Callable


class BaseConnector(ABC):
    """Base contract for pull connectors."""

    @abstractmethod
    async def fetch(self, since: str | None = None) -> list[dict[str, Any]]:
        """Fetch newly available records after a cursor."""


class FileTailerConnector(BaseConnector):
    """Tail Suricata/Wazuh JSON-lines files using inode and byte offsets."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._partial = b""
        self._inode: int | None = None
        self._offset = 0

    async def fetch(self, since: str | None = None) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._fetch_sync, since)

    def _fetch_sync(self, since: str | None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        stat = self.path.stat()
        cursor = {}
        if since:
            try:
                cursor = json.loads(since)
            except json.JSONDecodeError:
                cursor = {}
        cursor_inode = cursor.get("inode")
        if self._inode == stat.st_ino:
            offset = self._offset
        elif cursor_inode == stat.st_ino:
            offset = int(cursor.get("offset", 0))
        else:
            offset = 0
            self._partial = b""
        with self.path.open("rb") as handle:
            handle.seek(offset)
            raw = handle.read()
            data = self._partial + raw
        records: list[dict[str, Any]] = []
        complete = data.splitlines(keepends=True)
        self._partial = b""
        if complete and not complete[-1].endswith((b"\n", b"\r")):
            self._partial = complete.pop()
        for line in complete:
            if not line.strip():
                continue
            try:
                value = json.loads(line.decode("utf-8"))
                if isinstance(value, dict):
                    records.append(value)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        self._inode = stat.st_ino
        self._offset = offset + len(raw)
        self.cursor = json.dumps({"inode": stat.st_ino, "offset": self._offset})
        return records


class ConnectorRunner:
    """Poll a connector and pass each batch to a shared ingestion callback."""

    def __init__(self, connector: BaseConnector, callback: Callable[[list[dict[str, Any]]], Awaitable[None]], interval: float = 10.0) -> None:
        self.connector = connector
        self.callback = callback
        self.interval = max(1.0, interval)

    async def run(self, stop_event: asyncio.Event) -> None:
        cursor = None
        while not stop_event.is_set():
            events = await self.connector.fetch(cursor)
            cursor = getattr(self.connector, "cursor", cursor)
            if events:
                await self.callback(events)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass
