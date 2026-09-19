"""Machine-facing JSON event ingestion endpoint."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.models import UserDB
from database.session import get_db
from routers.auth import get_api_key_user
from services.ingestion import ingest_raw_events
from services.live_runtime import runtime

router = APIRouter(prefix="/api/v1/ingest", tags=["Streaming ingestion"])


class EventBatchRequest(BaseModel):
    """Bounded JSON payload for push ingestion."""
    events: List[Dict[str, Any]] = Field(..., min_length=1, max_length=1000)


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    request: EventBatchRequest,
    source: str = Query(default="generic", pattern=r"^[A-Za-z0-9_-]{1,40}$"),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Accept a bounded event batch using a tenant-scoped API key."""
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key is required")
    user: UserDB = get_api_key_user(api_key, db)
    try:
        return ingest_raw_events(
            db,
            user.id,
            source,
            request.events,
            queue=lambda user_id, alert_id: asyncio.create_task(runtime.enqueue(user_id, alert_id)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
