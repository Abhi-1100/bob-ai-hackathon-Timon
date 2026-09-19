"""Persistence service shared by push ingestion and future connectors."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Mapping, Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models import Alert as AlertDB, DeadLetterDB
from services.normalizer import AlertNormalizer, NormalizationError
from services.metrics import metrics

logger = logging.getLogger("ingestion")


def ingest_raw_events(db: Session, user_id: Any, source: str, events: Sequence[Mapping[str, Any]], queue=None) -> dict[str, int]:
    """Normalize, dead-letter, and idempotently persist a batch of events."""
    normalizer = AlertNormalizer(source)
    received = len(events)
    accepted = 0
    rejected = 0

    for raw_event in events:
        try:
            alert = normalizer.normalize(raw_event)
            dedupe_hash = normalizer.dedupe_hash(user_id, alert)
            existing = db.query(AlertDB.id).filter(AlertDB.dedupe_hash == dedupe_hash).first()
            if existing:
                continue
            try:
                with db.begin_nested():
                    row = AlertDB(
                        id=uuid.uuid4(), user_id=user_id, upload_id=None, timestamp=alert.timestamp,
                        src_ip=alert.src_ip, dst_ip=alert.dst_ip, event=alert.event,
                        severity=str(alert.severity), source=source, dedupe_hash=dedupe_hash,
                    )
                    db.add(row)
                    db.flush()
                accepted += 1
                metrics.mark_ingested(str(row.id))
                if queue is not None:
                    queue(user_id, row.id)
            except IntegrityError:
                # Another concurrent request won the unique-key race.
                logger.info("Duplicate event skipped after unique-key race (user_id=%s)", user_id)
        except (NormalizationError, ValueError, TypeError) as exc:
            rejected += 1
            db.add(DeadLetterDB(user_id=user_id, source=source, payload=json.dumps(raw_event, default=str), error=str(exc)))

    db.commit()
    return {"received": received, "accepted": accepted, "rejected": rejected}
