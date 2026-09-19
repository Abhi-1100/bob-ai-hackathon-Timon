"""Tenant-scoped Server-Sent Events stream."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database.models import UserDB
from database.session import get_db
from routers.auth import decode_access_token
from services.live_runtime import runtime

router = APIRouter(prefix="/api/v1", tags=["Live stream"])


def resolve_stream_user(token: str, db: Session) -> UserDB:
    """Validate a short-lived-compatible JWT query token and resolve its tenant."""
    payload = decode_access_token(token)
    try:
        user_id = payload.get("sub")
        user = db.query(UserDB).filter(UserDB.id == uuid.UUID(str(user_id))).first()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid stream token") from exc
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stream tenant not found")
    return user


@router.get("/stream")
async def stream_events(token: str = Query(..., min_length=20, max_length=4096), db: Session = Depends(get_db)):
    """Stream only events belonging to the JWT's tenant."""
    user = resolve_stream_user(token, db)
    queue = runtime.subscribe(user.id)

    async def event_generator() -> AsyncIterator[str]:
        try:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    event_type = event.get("type", "message")
                    yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            runtime.unsubscribe(user.id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
